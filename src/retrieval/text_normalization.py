"""Chuẩn hóa chuỗi để so khớp. Chỉ dùng khi so sánh, không sửa dữ liệu trong ES."""
import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Đưa chuỗi về dạng Unicode NFC (cùng một chữ có dấu có thể được mã hóa theo nhiều cách)."""
    return unicodedata.normalize("NFC", text or "")


def normalize_code(code) -> str:
    """Dạng so sánh của số ký hiệu: bỏ tiền tố "Số:", khoảng trắng, viết hoa, Ð (Latin) -> Đ.
    Ví dụ "Số: 154/2024/NĐ-CP" -> "154/2024/NĐ-CP"."""
    code = re.sub(r"^\s*s[ốo]\s*:?\s*", "", normalize_unicode(str(code or "")).replace("Ð", "Đ"), flags=re.I)
    return re.sub(r"\s+", "", code).upper()


def normalize_name(text: str) -> str:
    """Chuẩn hóa để so khớp tên văn bản: chữ thường, bỏ dấu câu, gộp khoảng trắng (giữ dấu tiếng Việt)."""
    text = normalize_unicode(text).lower().replace("&", " và ")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
