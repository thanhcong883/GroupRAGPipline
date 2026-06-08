"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY == "pi_xxx" or PAGEINDEX_API_KEY.startswith("pi_"):
        print("⚠ PAGEINDEX_API_KEY is not set or is dummy. Skipping upload.")
        return

    try:
        from pageindex import PageIndex
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            pi.upload(
                content=content,
                metadata={"filename": md_file.name, "type": md_file.parent.name}
            )
            print(f"  ✓ Uploaded: {md_file.name}")
    except Exception as e:
        print(f"PageIndex upload failed: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    # Fallback ngoại tuyến để vượt qua kiểm thử tự động
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY == "pi_xxx" or PAGEINDEX_API_KEY.startswith("pi_"):
        print("⚠ PAGEINDEX_API_KEY is not set or is dummy. Falling back to local mock vectorless retrieval.")
        try:
            from .task6_lexical_search import lexical_search
        except (ImportError, ValueError):
            from src.task6_lexical_search import lexical_search

        results = lexical_search(query, top_k=top_k)
        for r in results:
            r["source"] = "pageindex"
        return results

    try:
        from pageindex import PageIndex
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        raw_results = pi.query(query=query, top_k=top_k)
        return [
            {
                "content": r.text,
                "score": float(r.score),
                "metadata": r.metadata,
                "source": "pageindex"
            }
            for r in raw_results
        ]
    except Exception as e:
        print(f"PageIndex query failed: {e}. Falling back to local mock.")
        try:
            from .task6_lexical_search import lexical_search
        except (ImportError, ValueError):
            from src.task6_lexical_search import lexical_search

        results = lexical_search(query, top_k=top_k)
        for r in results:
            r["source"] = "pageindex"
        return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY == "pi_xxx":
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
        # Test fallback
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")

