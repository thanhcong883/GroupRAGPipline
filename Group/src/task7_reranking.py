"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

from typing import Optional


import os
import requests
from typing import Optional

def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    if not candidates:
        return []

    jina_key = os.getenv("JINA_API_KEY")
    if jina_key and jina_key != "jina_xxx" and not jina_key.startswith("jina_"):
        print("Using Jina AI Reranker API...")
        try:
            response = requests.post(
                "https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {jina_key}"},
                json={
                    "model": "jina-reranker-v2-base-multilingual",
                    "query": query,
                    "documents": [c["content"] for c in candidates],
                    "top_n": top_k
                },
                timeout=10
            )
            if response.status_code == 200:
                reranked = response.json()["results"]
                return [
                    {**candidates[r["index"]], "score": float(r["relevance_score"])}
                    for r in reranked
                ]
            else:
                print(f"Jina API returned error: {response.text}. Falling back to local reranker.")
        except Exception as e:
            print(f"Error calling Jina API: {e}. Falling back to local reranker.")

    # Fallback nội bộ: sử dụng mô hình local sentence-transformer để chấm điểm semantic similarity
    try:
        from .task5_semantic_search import get_embedding_model, cosine_similarity
    except (ImportError, ValueError):
        from src.task5_semantic_search import get_embedding_model, cosine_similarity

    model = get_embedding_model()
    query_emb = model.encode(query, show_progress_bar=False).tolist()

    results = []
    for item in candidates:
        content = item["content"]
        c_emb = model.encode(content, show_progress_bar=False).tolist()
        sim = cosine_similarity(query_emb, c_emb)
        new_item = item.copy()
        new_item["score"] = float(sim)
        results.append(new_item)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))
    """
    if not candidates:
        return []

    try:
        from .task5_semantic_search import get_embedding_model, cosine_similarity
    except (ImportError, ValueError):
        from src.task5_semantic_search import get_embedding_model, cosine_similarity

    model = get_embedding_model()

    # Đảm bảo tất cả candidates có embedding
    for c in candidates:
        if "embedding" not in c or c["embedding"] is None:
            c["embedding"] = model.encode(c["content"], show_progress_bar=False).tolist()

    selected = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining:
            relevance = cosine_similarity(query_embedding, candidates[idx]["embedding"])

            max_sim_to_selected = 0.0
            for sel_idx in selected:
                sim = cosine_similarity(candidates[idx]["embedding"], candidates[sel_idx]["embedding"])
                max_sim_to_selected = max(max_sim_to_selected, sim)

            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    rrf_scores = {}
    content_map = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in content_map:
                content_map[key] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = float(score)
        results.append(item)

    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        try:
            from .task5_semantic_search import get_embedding_model
        except (ImportError, ValueError):
            from src.task5_semantic_search import get_embedding_model
        model = get_embedding_model()
        query_embedding = model.encode(query, show_progress_bar=False).tolist()
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        # Nếu candidates được truyền dạng list of lists, gộp RRF
        if candidates and isinstance(candidates[0], list):
            return rerank_rrf(candidates, top_k)
        return candidates[:top_k]
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    # Test with dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")

