"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install markitdown

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
MIN_CONTENT_CHARS = 200


def extract_pdf_text_ocr(filepath: Path) -> str:
    """OCR fallback cho PDF scan (không có text layer)."""
    import fitz
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    doc = fitz.open(filepath)
    ocr = RapidOCR()
    pages: list[str] = []

    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:
            img = img[:, :, :3]

        result, _ = ocr(img)
        page_text = "\n".join(line[1] for line in (result or []))
        if page_text.strip():
            pages.append(page_text)

    return "\n\n".join(pages)


def convert_pdf_to_text(filepath: Path, md: MarkItDown) -> str:
    """Convert PDF: MarkItDown trước, OCR nếu PDF là bản scan."""
    result = md.convert(str(filepath))
    text = (result.text_content or "").strip()
    if len(text) >= MIN_CONTENT_CHARS:
        return text

    try:
        import fitz

        doc = fitz.open(filepath)
        text = "\n\n".join(page.get_text().strip() for page in doc).strip()
        if len(text) >= MIN_CONTENT_CHARS:
            print("  Fallback: PyMuPDF text extraction")
            return text
    except ImportError:
        pass

    print("  Fallback: OCR (PDF scan, co the mat vai phut)...")
    return extract_pdf_text_ocr(filepath)


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() not in (".pdf", ".docx", ".doc"):
            continue

        print(f"Converting: {filepath.name}")
        if filepath.suffix.lower() == ".pdf":
            content = convert_pdf_to_text(filepath, md)
        else:
            content = md.convert(str(filepath)).text_content or ""

        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(content, encoding="utf-8")
        print(f"  Saved: {output_path} ({output_path.stat().st_size:,} bytes)")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() != ".json":
            continue

        print(f"Converting: {filepath.name}")
        data = json.loads(filepath.read_text(encoding="utf-8"))
        output_path = output_dir / f"{filepath.stem}.md"

        header = f"# {data.get('title', 'Unknown')}\n\n"
        header += f"**Source:** {data.get('url', 'N/A')}\n"
        header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"

        content = header + data.get("content_markdown", "")
        output_path.write_text(content, encoding="utf-8")
        print(f"  Saved: {output_path} ({output_path.stat().st_size:,} bytes)")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\nDone! Output tai:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
