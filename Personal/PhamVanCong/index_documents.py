from pathlib import Path
import pickle

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# =====================
# Task 4 Configuration
# =====================

CHUNKING_STRATEGY = "RecursiveCharacterTextSplitter"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

INPUT_DIRS = [
    Path("data/standardized/legal"),
    Path("data/standardized/news"),
]

OUTPUT_DIR = Path("data/index")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "vector_index.pkl"


def load_markdown_files():
    documents = []

    for input_dir in INPUT_DIRS:
        for file_path in input_dir.glob("*.md"):
            text = file_path.read_text(encoding="utf-8")

            documents.append({
                "source": str(file_path),
                "filename": file_path.name,
                "content": text,
                "document_type": input_dir.name,
            })

    return documents


def main():
    print("=== Task 4: Chunking & Indexing ===")

    documents = load_markdown_files()
    print(f"Loaded documents: {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []

    for doc in documents:
        split_texts = splitter.split_text(doc["content"])

        for idx, chunk_text in enumerate(split_texts):
            chunks.append({
                "chunk_id": f"{doc['filename']}_{idx}",
                "content": chunk_text,
                "source": doc["source"],
                "filename": doc["filename"],
            })

    print(f"Created chunks: {len(chunks)}")

    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    texts = [chunk["content"] for chunk in chunks]

    print("Creating embeddings...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    vector_index = {
        "metadata": {
            "chunking_strategy": CHUNKING_STRATEGY,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "total_documents": len(documents),
            "total_chunks": len(chunks),
        },
        "chunks": chunks
    }

    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(vector_index, f)

    print(f"Saved vector index: {OUTPUT_FILE}")
    print("Task 4 completed successfully!")


if __name__ == "__main__":
    main()