"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from pathlib import Path

import json
from pathlib import Path
from rank_bm25 import BM25Okapi

DB_PATH = Path(__file__).parent.parent / "data" / "vector_store.json"

_corpus = None
_bm25 = None


def load_corpus() -> list[dict]:
    """Load corpus từ vector store hoặc tạo từ data/standardized/."""
    global _corpus
    if _corpus is None:
        if not DB_PATH.exists():
            print(f"⚠ Vector store file does not exist: {DB_PATH}. Building corpus...")
            try:
                from .task4_chunking_indexing import load_documents, chunk_documents
            except (ImportError, ValueError):
                from src.task4_chunking_indexing import load_documents, chunk_documents
            docs = load_documents()
            _corpus = chunk_documents(docs)
        else:
            try:
                with open(DB_PATH, "r", encoding="utf-8") as f:
                    _corpus = json.load(f)
            except Exception as e:
                print(f"Error loading vector store for lexical search: {e}")
                _corpus = []
    return _corpus


def get_bm25_index():
    """Lấy hoặc xây dựng BM25 index."""
    global _bm25
    if _bm25 is None:
        corpus = load_corpus()
        if not corpus:
            return None
        # Tokenize cơ bản cho tiếng Việt bằng cách lower, loại bỏ dấu câu đơn giản và split
        tokenized_corpus = []
        for doc in corpus:
            text = doc["content"].lower().replace(",", " ").replace(".", " ").replace(";", " ")
            tokenized_corpus.append(text.split())
        _bm25 = BM25Okapi(tokenized_corpus)
    return _bm25


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus (hàm tiện ích bổ trợ).
    """
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    corpus = load_corpus()
    bm25 = get_bm25_index()
    if not corpus or not bm25:
        return []

    # Tokenize câu truy vấn
    tokenized_query = query.lower().replace(",", " ").replace(".", " ").replace(";", " ").split()
    if not tokenized_query:
        return []

    scores = bm25.get_scores(tokenized_query)

    results = []
    for idx, score in enumerate(scores):
        results.append({
            "content": corpus[idx]["content"],
            "score": float(score),
            "metadata": corpus[idx].get("metadata", {})
        })

    # Sắp xếp giảm dần theo điểm số
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

