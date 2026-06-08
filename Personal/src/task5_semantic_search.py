"""Task 5 - Semantic Search Module."""

from .retrieval_utils import (
    corpus_tfidf_vectors,
    cosine_sparse,
    load_corpus,
    tfidf_vector,
    tokenize,
)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Return semantic-style retrieval results sorted by descending score.

    Task 4 documents the selected dense model as BAAI/bge-m3 (1024 dims). This
    module uses a deterministic local TF-IDF cosine fallback so the assignment
    runs on offline machines where the embedding model cannot be downloaded.
    The public API matches the required dense retriever shape.
    """
    corpus = load_corpus()
    if not query.strip() or top_k <= 0 or not corpus:
        return []

    query_vector = tfidf_vector(tokenize(query))
    scored: list[dict] = []
    for doc, doc_vector in zip(corpus, corpus_tfidf_vectors()):
        score = cosine_sparse(query_vector, doc_vector)
        if score > 0:
            scored.append(
                {
                    "content": doc["content"],
                    "score": float(score),
                    "metadata": doc.get("metadata", {}),
                }
            )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    for result in semantic_search("hinh phat ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
