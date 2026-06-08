from pathlib import Path
import json

from markitdown import MarkItDown

# =====================
# Directories
# =====================

LEGAL_INPUT = Path("data/landing/legal")
NEWS_INPUT = Path("data/landing/news")

LEGAL_OUTPUT = Path("data/standardized/legal")
NEWS_OUTPUT = Path("data/standardized/news")

LEGAL_OUTPUT.mkdir(parents=True, exist_ok=True)
NEWS_OUTPUT.mkdir(parents=True, exist_ok=True)

md = MarkItDown()

# =====================
# Convert PDFs
# =====================

print("=== Converting Legal PDFs ===")

for pdf_file in LEGAL_INPUT.glob("*.pdf"):

    print(f"Processing: {pdf_file.name}")

    result = md.convert(str(pdf_file))

    output_file = LEGAL_OUTPUT / f"{pdf_file.stem}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.text_content)

    print(f"Saved: {output_file}")

# =====================
# Convert News JSON
# =====================

print("\n=== Converting News JSON ===")

for json_file in NEWS_INPUT.glob("*.json"):

    print(f"Processing: {json_file.name}")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    markdown_content = f"""# {data.get('title', '')}

Nguồn: {data.get('url', '')}

Ngày crawl: {data.get('crawl_date', '')}

---

{data.get('content', '')}
"""

    output_file = NEWS_OUTPUT / f"{json_file.stem}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Saved: {output_file}")

print("\nDone!")
