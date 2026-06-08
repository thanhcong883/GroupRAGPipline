"""Task 10 - Generation with citations using Ollama qwen2.5:7b."""

from __future__ import annotations

import os
import re

from .task9_retrieval_pipeline import retrieve

# top_k=5 keeps enough evidence without flooding the small local model context.
TOP_K = 5
# top_p=0.9 allows natural Vietnamese wording while temperature keeps facts stable.
TOP_P = 0.9
TEMPERATURE = 0.3
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

SYSTEM_PROMPT = """Answer the question in Vietnamese using only the provided context.
Every factual claim must include a citation in brackets like [Source, Year].
If the context does not support the answer, say: I cannot verify this information.
Do not invent facts or sources."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Put the best chunk first and the second-best chunk last.

    Example for score order [1, 2, 3, 4, 5] -> [1, 3, 5, 4, 2].
    """
    if len(chunks) <= 2:
        return list(chunks)

    reordered: list[dict] = []
    for idx in range(0, len(chunks), 2):
        reordered.append(chunks[idx])

    last_even = len(chunks) - 1 if len(chunks) % 2 == 0 else len(chunks) - 2
    for idx in range(last_even, 0, -2):
        reordered.append(chunks[idx])

    return reordered


def _source_label(chunk: dict, index: int) -> str:
    metadata = chunk.get("metadata", {})
    source = metadata.get("source") or metadata.get("path") or f"Source {index}"
    year_match = re.search(r"(20\d{2}|19\d{2})", str(source) + " " + chunk.get("content", "")[:300])
    year = year_match.group(1) if year_match else "n.d."
    return f"{source}, {year}"


def format_context(chunks: list[dict]) -> str:
    """Format chunks with source labels so the LLM can cite precisely."""
    context_parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        label = _source_label(chunk, index)
        doc_type = metadata.get("type") or metadata.get("doc_type") or "unknown"
        context_parts.append(
            f"[Document {index} | Source: {label} | Type: {doc_type}]\n"
            f"{chunk.get('content', '').strip()}"
        )
    return "\n\n---\n\n".join(context_parts)


def _call_ollama(query: str, context: str) -> str:
    import requests

    user_message = f"Context:\n{context}\n\nQuestion: {query}"
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": TEMPERATURE, "top_p": TOP_P},
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


def _extractive_answer(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I cannot verify this information."

    sentences: list[str] = []
    for index, chunk in enumerate(chunks[:3], start=1):
        content = re.sub(r"\s+", " ", chunk.get("content", "")).strip()
        if not content:
            continue
        snippet = content[:450].rstrip()
        label = _source_label(chunk, index)
        sentences.append(f"{snippet} [{label}]")

    if not sentences:
        return "I cannot verify this information."

    return (
        f"Du lieu truy xuat cho cau hoi '{query}' cho thay: "
        + " ".join(sentences)
    )


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation with citations.

    Ollama qwen2.5:7b is used when available. The extractive fallback preserves
    citation behavior for offline tests and demos.
    """
    chunks = retrieve(query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)

    try:
        answer = _call_ollama(query, context)
    except Exception:
        answer = _extractive_answer(query, reordered)

    if not answer:
        answer = "I cannot verify this information."

    return {
        "answer": answer,
        "sources": reordered,
        "retrieval_source": chunks[0].get("source", "none") if chunks else "none",
    }


if __name__ == "__main__":
    result = generate_with_citation("Hinh phat tang tru trai phep chat ma tuy?")
    print(result["answer"])
