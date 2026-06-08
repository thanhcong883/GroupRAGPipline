"""
Task 4 — Chunking & Indexing vào Vector Store (ChromaDB).

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào ChromaDB local
"""

import json
import uuid
from functools import lru_cache
from pathlib import Path

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:
    RecursiveCharacterTextSplitter = None

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
CORPUS_PATH = Path(__file__).parent.parent / "data" / "chunks_corpus.json"

# =============================================================================
# CONFIGURATION
# =============================================================================

# RecursiveCharacterTextSplitter: an toàn cho cả văn bản pháp luật dài và báo chí.
# Cắt theo đoạn → câu → từ, tránh cắt giữa câu khi có thể.
CHUNK_SIZE = 500
# Overlap 50 ký tự (~10%) giữ ngữ cảnh giữa 2 chunk liền kề (vd: "Điều 248" không bị tách).
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# bge-m3: multilingual, hỗ trợ tiếng Việt tốt hơn MiniLM; 1024 dim.
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

VECTOR_STORE = "chromadb"
COLLECTION_NAME = "drug_law_docs"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """Đọc toàn bộ markdown files từ data/standardized/."""
    documents = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        rel_path = md_file.relative_to(STANDARDIZED_DIR)
        doc_type = rel_path.parts[0] if rel_path.parts else "unknown"
        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "path": str(rel_path).replace("\\", "/"),
                "type": doc_type,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chunk documents bằng RecursiveCharacterTextSplitter."""
    chunks: list[dict] = []
    for doc in documents:
        if RecursiveCharacterTextSplitter is not None:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            splits = splitter.split_text(doc["content"])
        else:
            text = doc["content"]
            step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
            splits = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), step)]
        for i, chunk_text in enumerate(splits):
            if not chunk_text.strip():
                continue
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": i,
                },
            })
    return chunks


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        show_progress_bar=len(texts) > 50,
        normalize_embeddings=True,
    )
    return [emb.tolist() for emb in embeddings]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Embed toàn bộ chunks bằng bge-m3."""
    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts)
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    return chunks


def get_chroma_collection(*, reset: bool = False):
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def save_corpus(chunks: list[dict]) -> None:
    """Lưu corpus chunks cho Task 6 (BM25)."""
    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    corpus = [
        {"content": c["content"], "metadata": c["metadata"]}
        for c in chunks
    ]
    CORPUS_PATH.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def index_to_vectorstore(chunks: list[dict], *, reset: bool = True) -> None:
    """Lưu chunks vào ChromaDB local."""
    collection = get_chroma_collection(reset=reset)

    ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [c["content"] for c in chunks]
    embeddings = [c["embedding"] for c in chunks]
    metadatas = [
        {
            "source": c["metadata"]["source"],
            "path": c["metadata"]["path"],
            "doc_type": c["metadata"]["type"],
            "chunk_index": c["metadata"]["chunk_index"],
        }
        for c in chunks
    ]

    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    save_corpus(chunks)


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE} -> {CHROMA_DIR}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print(f"Indexed to ChromaDB collection '{COLLECTION_NAME}'")
    print(f"Corpus saved: {CORPUS_PATH}")


if __name__ == "__main__":
    run_pipeline()
