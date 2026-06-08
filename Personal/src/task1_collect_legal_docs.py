"""
Task 1 — Thu thập văn bản pháp luật về ma tuý và các chất cấm.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản pháp luật (PDF/DOCX) từ các nguồn chính thống.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, có năm ban hành.

Gợi ý nguồn:
    - https://thuvienphapluat.vn
    - https://vanban.chinhphu.vn
    - https://luatvietnam.vn

Gợi ý văn bản:
    - Luật Phòng, chống ma tuý 2021 (73/2021/QH15)
    - Nghị định 105/2021/NĐ-CP
    - Bộ luật Hình sự 2015 (sửa đổi 2017) - Chương XX
    - Nghị định 57/2022/NĐ-CP về danh mục chất ma tuý
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


LEGAL_DOCUMENTS = [
    {
        "filename": "luat-phong-chong-ma-tuy-2021.pdf",
        "title": "Luật Phòng, chống ma tuý 2021 (73/2021/QH15)",
    },
    {
        "filename": "bo-luat-hinh-su-2015.pdf",
        "title": "Bộ luật Hình sự 2015 (sửa đổi 2017) — Chương XX: Tội phạm về ma tuý",
    },
    {
        "filename": "quy-dinh-danh-muc-chat-ma-tuy-va-tien-chat.pdf",
        "title": "Quy định các danh mục chất ma tuý và tiền chất",
    },
]


def list_legal_documents() -> list[Path]:
    """Liệt kê các file pháp luật đã thu thập."""
    valid_extensions = {".pdf", ".docx", ".doc"}
    return sorted(
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in valid_extensions
    )


if __name__ == "__main__":
    setup_directory()
    files = list_legal_documents()
    print(f"\nĐã thu thập {len(files)} văn bản pháp luật:")
    for f in files:
        print(f"  ✓ {f.name} ({f.stat().st_size:,} bytes)")
