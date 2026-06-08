"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Điền danh sách URL bài báo cần crawl
ARTICLE_URLS = [
    "https://tuoitre.vn/bat-nguoi-mau-an-tay-ca-si-chi-dan-co-tien-truc-phuong-do-lien-quan-ma-tuy-20241114114826655.htm",
    "https://tuoitre.vn/dien-vien-hai-huu-tin-bi-khoi-to-bat-tam-giam-vi-ma-tuy-20220617185327576.htm",
    "https://tuoitre.vn/cong-an-dua-ca-si-chu-bin-ve-tru-so-de-lam-ro-hanh-vi-nghi-lien-quan-ma-tuy-20240606194450472.htm",
    "https://thanhnien.vn/ca-si-chau-viet-cuong-linh-an-13-nam-tu-giam-ve-toi-giet-nguoi-185831663.htm",
    "https://thanhnien.vn/bat-giam-ca-si-chi-dan-nguoi-mau-an-tay-tiktoker-truc-phuong-do-lien-quan-ma-tuy-185241114132305664.htm",
]


async def crawl_article(url: str, crawler=None) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler

    if crawler is None:
        async with AsyncWebCrawler() as session:
            return await crawl_article(url, crawler=session)

    result = await crawler.arun(url=url)
    if not result.success:
        raise RuntimeError(f"Crawl that bai: {url} — {result.error_message}")

    metadata = result.metadata or {}
    title = metadata.get("title") or metadata.get("og:title") or "Unknown"

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": result.markdown or "",
    }


def url_to_filename(url: str, index: int) -> str:
    """Tạo tên file từ URL slug, fallback article_XX."""
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"\.(htm|html)$", "", slug, flags=re.IGNORECASE)
    slug = slug[:80] if slug else f"article_{index:02d}"
    return f"{slug}.json"


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    from crawl4ai import AsyncWebCrawler

    setup_directory()

    async with AsyncWebCrawler() as crawler:
        for i, url in enumerate(ARTICLE_URLS, 1):
            print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
            article = await crawl_article(url, crawler=crawler)

            filename = url_to_filename(url, i)
            filepath = DATA_DIR / filename
            filepath.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"  Saved: {filepath} ({filepath.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
