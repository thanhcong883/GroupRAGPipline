import asyncio
import json
from datetime import datetime
from pathlib import Path

from crawl4ai import AsyncWebCrawler

ARTICLE_URLS = [
    "https://vietnamnet.vn/ngoai-nguyen-cong-tri-nhung-nghe-si-nao-tung-bi-bat-vi-ma-tuy-2424971.html",
    "https://vietnamnet.vn/ca-si-miu-le-bi-cong-an-dua-ve-tru-so-lam-viec-vi-nghi-van-ma-tuy-2514722.html",
    "https://thanhnien.vn/ca-si-long-nhat-bi-bat-showbiz-viet-lien-tiep-chan-dong-vi-ma-tuy-18526052013032001.htm",
    "https://vietnamnet.vn/ca-si-son-ngoc-minh-vua-bi-bat-vi-ma-tuy-tung-bi-chi-trich-du-doi-2517569.html",
    "https://dantri.com.vn/phap-luat/ca-si-chu-bin-bi-tam-giu-vi-lien-quan-den-ma-tuy-20240606183158183.htm",
]

OUTPUT_DIR = Path("data/landing/news")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    async with AsyncWebCrawler() as crawler:

        for idx, url in enumerate(ARTICLE_URLS, start=1):

            print(f"\n=== Crawling article {idx} ===")
            print(url)

            result = await crawler.arun(url=url)

            article_data = {
                "url": url,
                "crawl_date": datetime.now().isoformat(),
                "title": (
                    result.metadata.get("title", "")
                    if result.metadata
                    else ""
                ),
                "content": result.markdown,
            }

            output_file = OUTPUT_DIR / f"article_{idx}.json"

            with open(
                output_file,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    article_data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(f"Saved: {output_file}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())