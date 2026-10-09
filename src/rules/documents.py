"""Luật về văn bản pháp luật: số ký hiệu, Điều/Khoản/Điểm, tên và viết tắt văn bản, cấu trúc tiêu đề, thứ tự ưu tiên
khi nhiều văn bản cùng khớp, nhãn hiệu lực gửi cho LLM."""
import re
from typing import List, Optional

# SỐ KÝ HIỆU VĂN BẢN 
# Số ký hiệu đầy đủ: "12/2022/NĐ-CP", "52/2014/QH13", "08/2021/NQ-UBTVQH15"
code_pattern = re.compile(r"(?<![\w/])(\d{1,5}(?:/[0-9A-Za-zÀ-ỹĐđ&\-]+)+)", re.UNICODE)

# Số ký hiệu phải có chữ cái (để phân biệt với ngày tháng thuần số như 15/12/2025)
letter_pattern = re.compile(r"[A-Za-zÀ-ỹĐđ]")

# Số ký hiệu rút gọn số/năm: "168/2024", "nghị định 100/2019", "NĐ 100/2019" (loại văn bản đứng trước là tùy chọn)
partial_code_pattern = re.compile(
    r"(?:(nghị định|nđ|thông tư liên tịch|thông tư|tt|quyết định|qđ|nghị quyết|nq|luật|bộ luật|chỉ thị)\s+(?:số\s+)?)?"
    r"(?<![\w/])(?<!tháng )(?<!ngày )(\d{1,5})/((?:19|20)\d{2})(?![\w/])",
    re.IGNORECASE | re.UNICODE,
)

# Số hiệu chỉ có số, không có năm (cách gọi phổ biến): "Nghị định 218", "theo Thông tư số 05".
# Bắt buộc có loại văn bản đứng trước; không nhận số đi kèm đơn vị ("quyết định 30 ngày")
number_only_code_pattern = re.compile(
    r"(?<![\w/])(nghị định|thông tư liên tịch|thông tư|quyết định|nghị quyết|nđ|qđ)\s+(?:số\s+)?(\d{1,4})"
    r"(?![\d/]|[.,]\d|\s*(?:ngày|tháng|năm|giờ|lần|người|%|đồng|triệu|tỷ))",
    re.IGNORECASE | re.UNICODE,
)

# Loại văn bản đứng trước số hiệu rút gọn -> phần viết tắt phải có trong số ký hiệu đầy đủ
document_type_markers = {
    "nghị định": "NĐ",
    "nđ": "NĐ",
    "thông tư liên tịch": "TTLT",
    "thông tư": "TT",
    "tt": "TT",
    "quyết định": "QĐ",
    "qđ": "QĐ",
    "nghị quyết": "NQ",
    "nq": "NQ",
    "luật": "QH",
    "bộ luật": "QH",
    "chỉ thị": "CT",
}


# ĐIỀU / KHOẢN / ĐIỂM 
# Căn cứ dạng "Điểm a Khoản 2 Điều 105" (điểm và khoản là tùy chọn); không nhận "Điều 5/..." (số ký hiệu)
article_pattern = re.compile(
    r"(?:điểm\s+([a-zđ])\s*,?\s*)?(?:khoản\s+(\d{1,3})\s*,?\s*)?điều\s+(\d{1,4})(?!\s*/)",
    re.IGNORECASE | re.UNICODE,
)


# VIẾT TẮT VÀ TÊN GỌI THÔNG DỤNG 
# Viết tắt / cách gọi thông dụng -> tên chuẩn ở đầu tiêu đề văn bản trong ES
document_aliases = {
    "blhs": "Bộ luật Hình sự",
    "bộ luật hình sự": "Bộ luật Hình sự",
    "luật hình sự": "Bộ luật Hình sự",
    "blds": "Bộ luật Dân sự",
    "bộ luật dân sự": "Bộ luật Dân sự",
    "luật dân sự": "Bộ luật Dân sự",
    "blld": "Bộ luật Lao động",
    "bllđ": "Bộ luật Lao động",
    "bộ luật lao động": "Bộ luật Lao động",
    "luật lao động": "Bộ luật Lao động",
    "bltths": "Bộ luật Tố tụng hình sự",
    "bộ luật tố tụng hình sự": "Bộ luật Tố tụng hình sự",
    "luật tố tụng hình sự": "Bộ luật Tố tụng hình sự",
    "blttds": "Bộ luật Tố tụng dân sự",
    "bộ luật tố tụng dân sự": "Bộ luật Tố tụng dân sự",
    "luật tố tụng dân sự": "Bộ luật Tố tụng dân sự",
    "bộ luật hàng hải": "Bộ luật Hàng hải",
    "hngđ": "Luật Hôn nhân và gia đình",
    "hngd": "Luật Hôn nhân và gia đình",
    "hn&gđ": "Luật Hôn nhân và gia đình",
    "hn và gđ": "Luật Hôn nhân và gia đình",
    "xlvphc": "Luật Xử lý vi phạm hành chính",
    "bhxh": "Luật Bảo hiểm xã hội",
    "bhyt": "Luật Bảo hiểm y tế",
}

def build_alias_pattern(aliases) -> re.Pattern:
    """Regex tìm viết tắt / tên thông dụng trong câu hỏi."""
    escaped_aliases = []
    for alias in aliases:
        escaped_aliases.append(re.escape(alias))
    # Xếp từ dài đến ngắn để tên dài được ưu tiên khớp trước
    escaped_aliases.sort(key=len, reverse=True)
    alternatives = "|".join(escaped_aliases)
    return re.compile(r"(?<!\w)(?:luật\s+)?(" + alternatives + r")(?!\w)", re.IGNORECASE | re.UNICODE)


alias_pattern = build_alias_pattern(document_aliases)


# TÊN VĂN BẢN VÀ NĂM 
# Tên dạng "Luật <Tên>": lấy rộng đoạn chữ phía sau (tên luật có thể chứa "và", "của"...), rồi so khớp với tiêu đề
# trong ES để lấy tên đúng. Nghị định / Thông tư / Quyết định chỉ nhận qua số ký hiệu vì các cụm như
# "quyết định hành chính" là thuật ngữ chung.
document_name_pattern = re.compile(
    r"(?<![\w])(?<!pháp )(Hiến pháp|Bộ luật|Luật|Pháp lệnh)\s+(?!số\b|năm\b)([^\W\d_]+(?:,?\s+[^\W\d_]+){0,13})",
    re.IGNORECASE | re.UNICODE,
)

# Năm đứng sau tên văn bản: "Luật Đất đai năm 2024", "Luật Đất đai 2024"
year_after_pattern = re.compile(r"\s*(?:năm\s+)?((?:19|20)\d{2})(?![\d/])")

# Một từ là năm (19xx hoặc 20xx)
year_word_pattern = re.compile(r"(19|20)\d{2}")


def document_type_of(name_words: List[str]) -> str:
    """Loại văn bản từ các từ đầu của tên văn bản (đã chuẩn hóa thường).
    Ví dụ: ["bộ", "luật", "hình", "sự"] -> "bộ luật"; ["hiến", "pháp", "2013"] -> "hiến pháp"; ["luật", "đất", "đai"] -> "luật".
    """
    if name_words[:2] == ["bộ", "luật"]:
        return "bộ luật"
    if name_words[0] == "hiến":
        return "hiến pháp"
    return name_words[0]


def title_name_words(title_words: List[str]) -> List[str]:
    """Giữ phần tên cốt lõi trong các từ của tiêu đề văn bản (đã chuẩn hóa).
    Ví dụ: "luật cư trú số 68 2020 qh14" -> ["luật", "cư", "trú"] (cắt từ "số" trở đi);
    "luật khám bệnh chữa bệnh 2023" -> ["luật", "khám", "bệnh", "chữa", "bệnh"] (bỏ năm ở cuối).
    """
    words = list(title_words)
    # Từ "số" trở đi thường là số hiệu, ngày ban hành
    if "số" in words:
        words = words[: words.index("số")]
    # Bỏ năm ban hành ở cuối
    while words and year_word_pattern.fullmatch(words[-1]):
        words.pop()
    return words


# THỨ TỰ ƯU TIÊN KHI NHIỀU VĂN BẢN CÙNG KHỚP 

# Hiệu lực: số nhỏ được ưu tiên
status_rank = {"Còn hiệu lực": 0, "Hết hiệu lực một phần": 1}

# Ngày dạng DD/MM/YYYY
day_month_year_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")


def document_preference_key(source: dict, year: Optional[int]):
    """Khóa sắp xếp để chọn văn bản phù hợp nhất trong nhiều văn bản cùng khớp (giá trị nhỏ đứng trước):
    1. trùng năm người dùng hỏi (theo ngày ban hành hoặc số ký hiệu), nếu có;
    2. hiệu lực: Còn hiệu lực > Hết hiệu lực một phần > khác;
    3. cấp ban hành: Trung ương > Địa phương;
    4. văn bản mới hơn.
    """
    # Năm ban hành: ngày có thể ở dạng DD/MM/YYYY hoặc YYYY-MM-DD
    issue_date = str(source.get("ngay_ban_hanh") or "")
    if day_month_year_pattern.match(issue_date):
        issue_year = issue_date[-4:]
    else:
        issue_year = issue_date[:4]

    # 1. Trùng năm người dùng hỏi
    year_match = 1
    if year:
        same_issue_year = issue_year == str(year)
        year_in_code = f"/{year}/" in str(source.get("so_ky_hieu"))
        if same_issue_year or year_in_code:
            year_match = 0

    # 2. Hiệu lực
    status = status_rank.get(source.get("tinh_trang_hieu_luc"), 2)

    # 3. Cấp ban hành
    if source.get("pham_vi") == "Trung ương":
        central = 0
    else:
        central = 1

    # 4. Văn bản mới hơn đứng trước (năm càng lớn, giá trị càng nhỏ)
    if issue_year.isdigit():
        newest_first = -int(issue_year)
    else:
        newest_first = 0

    return (year_match, status, central, newest_first)


# NHÃN HIỆU LỰC GỬI CHO LLM 

# Nhãn thêm vào trích lục của văn bản người dùng nêu đích danh (số ký hiệu / tên) nhưng không ở trạng thái đang áp dụng
asked_document_note = ("VĂN BẢN ĐƯỢC HỎI ĐÍCH DANH: được dùng để trả lời câu hỏi về chính văn bản này, "
                       "nhưng phải nói rõ tình trạng hiệu lực ngay ở mục 1")


def status_label(status: str, asked_by_name: bool = False) -> str:
    """Trạng thái hiệu lực trong ES -> nhãn rõ ràng cho LLM biết văn bản có được dùng làm căn cứ hay không.
    asked_by_name=True: văn bản được hỏi đích danh -> vẫn được dùng, kèm yêu cầu nói rõ hiệu lực."""
    label = base_status_label(status)
    usable_as_basis = label == "ĐANG CÓ HIỆU LỰC" or label.startswith("HẾT HIỆU LỰC MỘT PHẦN")
    if asked_by_name and not usable_as_basis:
        # Giữ phần tên trạng thái ("ĐÃ HẾT HIỆU LỰC"), thay phần "không dùng làm căn cứ" bằng ghi chú hỏi đích danh
        status_name = label.split(" - ")[0]
        return f"{status_name} - {asked_document_note}"
    return label


def base_status_label(status: str) -> str:
    """Nhãn hiệu lực theo giá trị tinh_trang_hieu_luc ("Chưa xác định" phải xét trước "chưa")."""
    text = str(status).strip().lower()
    if "chưa xác định" in text or "không xác định" in text:
        return "KHÔNG RÕ HIỆU LỰC"
    if "chưa" in text:
        return "CHƯA CÓ HIỆU LỰC - không dùng làm căn cứ áp dụng"
    if "một phần" in text:
        return "HẾT HIỆU LỰC MỘT PHẦN - chưa xác định nội dung này còn hiệu lực hay không"
    if "hết hiệu lực" in text or "bãi bỏ" in text:
        return "ĐÃ HẾT HIỆU LỰC - không dùng làm căn cứ áp dụng"
    if "ngưng" in text:
        return "NGƯNG HIỆU LỰC - không dùng làm căn cứ áp dụng"
    if "còn hiệu lực" in text:
        return "ĐANG CÓ HIỆU LỰC"
    return "KHÔNG RÕ HIỆU LỰC"
