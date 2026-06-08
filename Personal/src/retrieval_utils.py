"""Shared local retrieval helpers for the individual RAG tasks."""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CORPUS_PATH = PROJECT_DIR / "data" / "chunks_corpus.json"
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"


def tokenize(text: str) -> list[str]:
    """Simple Unicode tokenization that works for Vietnamese and mojibake text."""
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


@lru_cache(maxsize=1)
def load_corpus() -> list[dict]:
    """Load chunk corpus, rebuilding from markdown files when the JSON is absent."""
    if CORPUS_PATH.exists():
        data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        return [
            {
                "content": item.get("content", ""),
                "metadata": item.get("metadata", {}),
            }
            for item in data
            if item.get("content")
        ]

    corpus: list[dict] = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        rel_path = md_file.relative_to(STANDARDIZED_DIR)
        corpus.append(
            {
                "content": text,
                "metadata": {
                    "source": md_file.name,
                    "path": str(rel_path).replace("\\", "/"),
                    "type": rel_path.parts[0] if rel_path.parts else "unknown",
                    "chunk_index": 0,
                },
            }
        )
    return corpus


@lru_cache(maxsize=1)
def corpus_document_frequencies() -> tuple[dict[str, int], int]:
    corpus = load_corpus()
    df: dict[str, int] = {}
    for doc in corpus:
        for token in set(tokenize(doc["content"])):
            df[token] = df.get(token, 0) + 1
    return df, len(corpus)


def tfidf_vector(tokens: list[str]) -> dict[str, float]:
    df, n_docs = corpus_document_frequencies()
    if not tokens or n_docs == 0:
        return {}

    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1

    total = len(tokens)
    vector: dict[str, float] = {}
    for token, count in counts.items():
        idf = math.log((n_docs + 1) / (df.get(token, 0) + 1)) + 1.0
        vector[token] = (count / total) * idf
    return vector


def cosine_sparse(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a).intersection(b)
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@lru_cache(maxsize=1)
def corpus_tfidf_vectors() -> list[dict[str, float]]:
    return [tfidf_vector(tokenize(doc["content"])) for doc in load_corpus()]


def result_key(item: dict) -> str:
    metadata = item.get("metadata", {})
    return "|".join(
        [
            str(metadata.get("path") or metadata.get("source") or ""),
            str(metadata.get("chunk_index") or ""),
            item.get("content", "")[:120],
        ]
    )
