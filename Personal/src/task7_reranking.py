"""Task 7 - Reranking Module."""

from __future__ import annotations

from .retrieval_utils import cosine_sparse, result_key, tfidf_vector, tokenize


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score candidates with a local cross-encoder-style lexical relevance proxy.

    A real submission can swap this for Jina/Qwen reranker. The deterministic
    proxy combines query-document cosine and incoming retrieval score, so it is
    stable for tests and offline demos.
    """
    if top_k <= 0:
        return []

    query_vector = tfidf_vector(tokenize(query))
    reranked: list[dict] = []
    for candidate in candidates:
        content = candidate.get("content", "")
        relevance = cosine_sparse(query_vector, tfidf_vector(tokenize(content)))
        original_score = float(candidate.get("score", 0.0))
        score = 0.75 * relevance + 0.25 * original_score
        item = {**candidate, "score": float(score), "rerank_method": "local_cross_encoder_proxy"}
        reranked.append(item)

    reranked.sort(key=lambda item: item["score"], reverse=True)
    return reranked[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """Select candidates with Maximal Marginal Relevance when embeddings exist."""
    if top_k <= 0:
        return []
    if not candidates:
        return []

    def cosine_dense(a: list[float], b: list[float]) -> float:
        import math

        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    selected: list[int] = []
    remaining = list(range(len(candidates)))
    while remaining and len(selected) < top_k:
        best_idx = remaining[0]
        best_score = float("-inf")
        for idx in remaining:
            embedding = candidates[idx].get("embedding", [])
            relevance = cosine_dense(query_embedding, embedding)
            diversity_penalty = 0.0
            for selected_idx in selected:
                diversity_penalty = max(
                    diversity_penalty,
                    cosine_dense(embedding, candidates[selected_idx].get("embedding", [])),
                )
            mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
            if mmr_score > best_score:
                best_idx = idx
                best_score = mmr_score
        selected.append(best_idx)
        remaining.remove(best_idx)

    return [{**candidates[i], "score": float(candidates[i].get("score", 0.0))} for i in selected]


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """Merge ranked lists with Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            key = result_key(item)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            items.setdefault(key, item)

    merged: list[dict] = []
    for key, score in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_k]:
        merged.append({**items[key], "score": float(score)})
    return merged


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    """Unified reranking interface."""
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    if method == "mmr":
        return rerank_cross_encoder(query, candidates, top_k)
    raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    docs = [
        {"content": "Dieu 248: Toi tang tru trai phep chat ma tuy", "score": 0.8, "metadata": {}},
        {"content": "Nghe si bi bat vi ma tuy", "score": 0.7, "metadata": {}},
    ]
    for result in rerank("hinh phat ma tuy", docs):
        print(f"[{result['score']:.3f}] {result['content']}")
