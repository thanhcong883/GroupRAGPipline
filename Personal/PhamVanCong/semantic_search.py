from pathlib import Path
import pickle
import numpy as np

from sentence_transformers import SentenceTransformer


INDEX_FILE = Path("data/index/vector_index.pkl")


def load_index():
    with open(INDEX_FILE, "rb") as f:
        return pickle.load(f)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    vector_index = load_index()
    metadata = vector_index["metadata"]
    chunks = vector_index["chunks"]

    model = SentenceTransformer(metadata["embedding_model"])

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    results = []

    for chunk in chunks:
        chunk_embedding = np.array(chunk["embedding"])
        score = float(np.dot(query_embedding, chunk_embedding))

        results.append({
            "content": chunk["content"],
            "score": score,
            "metadata": {
                "chunk_id": chunk.get("chunk_id"),
                "source": chunk.get("source"),
                "filename": chunk.get("filename"),
            }
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    query = "Nghệ sĩ nào từng bị bắt vì ma túy?"
    results = semantic_search(query, top_k=5)

    print(f"Query: {query}\n")

    for i, item in enumerate(results, start=1):
        print(f"=== Result {i} ===")
        print(f"Score: {item['score']:.4f}")
        print(f"Source: {item['metadata']['filename']}")
        print(item["content"][:500])
        print()