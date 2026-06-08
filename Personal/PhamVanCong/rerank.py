from semantic_search import semantic_search
from lexical_search import lexical_search


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score and re-order candidates based on relevance to query.

    Method: RRF - Reciprocal Rank Fusion
    Why:
    - No API key required
    - No heavy local reranker model
    - Good for combining semantic search and BM25
    """
    k = 60
    fused = {}

    for rank, item in enumerate(candidates, start=1):
        metadata = item.get("metadata", {})
        key = metadata.get("chunk_id") or item["content"][:100]

        if key not in fused:
            fused[key] = {
                "content": item["content"],
                "score": 0.0,
                "metadata": metadata,
            }

        fused[key]["score"] += 1 / (k + rank)

    results = list(fused.values())
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_k]


def hybrid_candidates(query: str, top_k_each: int = 10) -> list[dict]:
    semantic_results = semantic_search(query, top_k=top_k_each)
    lexical_results = lexical_search(query, top_k=top_k_each)

    combined = []

    for item in semantic_results:
        item["metadata"]["retrieval_method"] = "semantic"
        combined.append(item)

    for item in lexical_results:
        item["metadata"]["retrieval_method"] = "lexical_bm25"
        combined.append(item)

    return combined


if __name__ == "__main__":
    query = "Nguyễn Công Trí bị bắt vì ma túy như thế nào?"

    candidates = hybrid_candidates(query, top_k_each=10)
    results = rerank(query, candidates, top_k=5)

    print(f"Query: {query}\n")

    for i, item in enumerate(results, start=1):
        print(f"=== Reranked Result {i} ===")
        print(f"RRF Score: {item['score']:.4f}")
        print(f"Source: {item['metadata'].get('filename')}")
        print(item["content"][:500])
        print()