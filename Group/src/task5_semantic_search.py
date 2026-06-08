"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

DB_PATH = Path(__file__).parent.parent / "data" / "vector_store.json"

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from .task4_chunking_indexing import EMBEDDING_MODEL
        except (ImportError, ValueError):
            from src.task4_chunking_indexing import EMBEDDING_MODEL
        print(f"Loading embedding model for search: {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def dot_product(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return sum(x * x for x in a) ** 0.5


def cosine_similarity(a, b):
    na = norm(a)
    nb = norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return dot_product(a, b) / (na * nb)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not DB_PATH.exists():
        print(f"⚠ Vector store file does not exist: {DB_PATH}. Please run Task 4 first.")
        return []

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except Exception as e:
        print(f"Error reading vector store: {e}")
        return []

    if not chunks:
        return []

    model = get_embedding_model()
    query_embedding = model.encode(query, show_progress_bar=False).tolist()

    results = []
    for chunk in chunks:
        chunk_emb = chunk.get("embedding")
        if chunk_emb is None:
            continue
        score = cosine_similarity(query_embedding, chunk_emb)
        results.append({
            "content": chunk["content"],
            "score": float(score),
            "metadata": chunk.get("metadata", {})
        })

    # Sắp xếp giảm dần theo score similarity
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

