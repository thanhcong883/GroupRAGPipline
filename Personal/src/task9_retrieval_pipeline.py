"""Task 9 - Complete retrieval pipeline."""

from __future__ import annotations

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Run semantic + lexical retrieval, merge with RRF, rerank, then fallback.
    """
    if top_k <= 0:
        return []

    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 3)
    merged = [{**item, "source": "hybrid"} for item in merged]

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        final_results = [{**item, "source": "hybrid"} for item in final_results]
    else:
        final_results = merged[:top_k]

    best_score = float(final_results[0]["score"]) if final_results else 0.0
    if not final_results or best_score < score_threshold:
        return pageindex_search(query, top_k=top_k)

    final_results.sort(key=lambda item: item["score"], reverse=True)
    return final_results[:top_k]


if __name__ == "__main__":
    for result in retrieve("hinh phat ma tuy", top_k=3):
        print(f"[{result['score']:.3f}] [{result['source']}] {result['content'][:100]}...")
