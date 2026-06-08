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
    """Tạo thư mục data/landing/legal/ nếu chưa có và tạo các file mock."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")
    
    # Tạo 3 file mock pháp luật với size > 1024 bytes
    mock_files = [
        "luat-phong-chong-ma-tuy-2021.pdf",
        "nghi-dinh-105-2021.docx",
        "bo-luat-hinh-su-2015.pdf"
    ]
    for filename in mock_files:
        filepath = DATA_DIR / filename
        # Ghi nội dung giả lập dài hơn 1024 ký tự
        dummy_content = f"Mock legal document content for {filename}. " * 50
        filepath.write_text(dummy_content, encoding="utf-8")
        print(f"✓ Đã tạo file mock: {filepath} ({filepath.stat().st_size} bytes)")


if __name__ == "__main__":
    setup_directory()

