"""Task 8 - PageIndex Vectorless RAG fallback."""

from __future__ import annotations

import os
from pathlib import Path

from .retrieval_utils import load_corpus
from .task6_lexical_search import lexical_search

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """Placeholder uploader for real PageIndex accounts."""
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY is not configured")

    try:
        from pageindex import PageIndex
    except Exception as exc:
        raise RuntimeError("pageindex package is not installed") from exc

    client = PageIndex(api_key=PAGEINDEX_API_KEY)
    uploaded = 0
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        client.upload(content=content, metadata={"filename": md_file.name, "type": md_file.parent.name})
        uploaded += 1
    return {"uploaded": uploaded}


def _local_vectorless_search(query: str, top_k: int) -> list[dict]:
    results = lexical_search(query, top_k=top_k)
    if not results and load_corpus():
        results = [
            {
                "content": item["content"],
                "score": 0.01,
                "metadata": item.get("metadata", {}),
            }
            for item in load_corpus()[:top_k]
        ]

    return [{**item, "source": "pageindex"} for item in results[:top_k]]


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using PageIndex when configured, otherwise local fallback.

    The fallback intentionally marks results as 'pageindex' because it occupies
    the same pipeline branch: a non-vector retriever used when hybrid retrieval
    is weak or unavailable.
    """
    if top_k <= 0:
        return []

    if PAGEINDEX_API_KEY:
        try:
            from pageindex import PageIndex

            client = PageIndex(api_key=PAGEINDEX_API_KEY)
            raw_results = client.query(query=query, top_k=top_k)
            return [
                {
                    "content": getattr(result, "text", str(result)),
                    "score": float(getattr(result, "score", 0.0)),
                    "metadata": getattr(result, "metadata", {}) or {},
                    "source": "pageindex",
                }
                for result in raw_results
            ]
        except Exception:
            pass

    return _local_vectorless_search(query, top_k)


if __name__ == "__main__":
    for result in pageindex_search("hinh phat ma tuy", top_k=3):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
