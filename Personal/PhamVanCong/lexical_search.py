from pathlib import Path
import pickle
import re

from rank_bm25 import BM25Okapi


INDEX_FILE = Path("data/index/vector_index.pkl")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    return re.findall(r"\w+", text, flags=re.UNICODE)


def load_index():
    with open(INDEX_FILE, "rb") as f:
        return pickle.load(f)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    BM25 lexical search over local chunks.

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    vector_index = load_index()
    chunks = vector_index["chunks"]

    corpus = [chunk["content"] for chunk in chunks]
    tokenized_corpus = [tokenize(doc) for doc in corpus]

    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    results = []

    for chunk, score in zip(chunks, scores):
        results.append({
            "content": chunk["content"],
            "score": float(score),
            "metadata": {
                "chunk_id": chunk.get("chunk_id"),
                "source": chunk.get("source"),
                "filename": chunk.get("filename"),
            }
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    query = "Nguyễn Công Trí ma túy"
    results = lexical_search(query, top_k=5)

    print(f"Query: {query}\n")

    for i, item in enumerate(results, start=1):
        print(f"=== Result {i} ===")
        print(f"Score: {item['score']:.4f}")
        print(f"Source: {item['metadata']['filename']}")
        print(item["content"][:500])
        print()