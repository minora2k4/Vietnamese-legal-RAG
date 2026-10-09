"""Phân tích câu hỏi bằng rule base (src/rules): lấy metadata dùng cho truy vấn (số ký hiệu, Điều/Khoản/Điểm,
tên văn bản, năm, tỉnh/thành), tách câu hỏi ghép thành câu hỏi con, bổ sung thuật ngữ pháp lý."""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.retrieval.text_normalization import normalize_unicode
from src.rules.documents import (alias_pattern, article_pattern, code_pattern, document_aliases, document_name_pattern,
                                 document_type_markers, letter_pattern, number_only_code_pattern, partial_code_pattern,
                                 year_after_pattern)
from src.rules.legal_terms import lay_to_legal_terms
from src.rules.places import province_canonical_names, province_pattern
from src.rules.questions import (comparison_patterns, condition_reference_pattern, multi_part_split_pattern,
                                 question_tail_pattern, question_word_pattern, subject_end_pattern,
                                 subject_reference_pattern)


@dataclass
class ArticleReference:
    """Điều (và Khoản, Điểm nếu có) được nhắc trong câu hỏi."""
    dieu: str
    khoan: Optional[str] = None
    diem: Optional[str] = None


@dataclass
class DocumentMention:
    """Tên văn bản được nhắc trong câu hỏi."""
    name: str                      # tên chuẩn (từ bảng viết tắt, khớp chính xác) hoặc đoạn chữ bắt đầu bằng loại văn bản
    year: Optional[int] = None     # năm đứng ngay sau tên ("Luật Đất đai 2024")
    exact: bool = False            # True nếu name là tên chuẩn lấy từ document_aliases


@dataclass
class ParsedQuery:
    codes: List[str] = field(default_factory=list)                                # số ký hiệu đầy đủ
    partial_codes: List[Tuple[str, Optional[str]]] = field(default_factory=list)  # ("168/2024", "NĐ"), ("218", "NĐ")
    articles: List[ArticleReference] = field(default_factory=list)
    documents: List[DocumentMention] = field(default_factory=list)
    provinces: List[str] = field(default_factory=list)

    @property
    def has_document_reference(self) -> bool:
        """Câu hỏi có nhắc tới một văn bản cụ thể (số ký hiệu hoặc tên)."""
        return bool(self.codes or self.partial_codes or self.documents)


def year_after(text: str, position: int) -> Optional[int]:
    """Năm đứng ngay sau vị trí position (sau tên văn bản), nếu có."""
    match = year_after_pattern.match(text[position:])
    if match:
        return int(match.group(1))
    return None


def overlaps_any(start: int, end: int, spans: List[Tuple[int, int]]) -> bool:
    """Đoạn [start, end) có chồng lên một trong các đoạn spans không."""
    for span_start, span_end in spans:
        if span_start <= start < span_end:
            return True
        if start <= span_start < end:
            return True
    return False


def parse_query(query: str) -> ParsedQuery:
    text = normalize_unicode(query).strip()
    parsed = ParsedQuery()

    # Số ký hiệu đầy đủ ("168/2024/NĐ-CP"); bỏ ngày tháng thuần số (không có chữ cái)
    for raw_code in code_pattern.findall(text):
        if not letter_pattern.search(raw_code):
            continue
        code = raw_code.strip("-/")
        if code not in parsed.codes:
            parsed.codes.append(code)

    # Số hiệu rút gọn số/năm ("Nghị định 168/2024"), kèm loại văn bản đứng trước nếu có
    covered_codes = " ".join(parsed.codes)
    for document_type, number, year in partial_code_pattern.findall(text):
        code = f"{number}/{year}"
        if code in covered_codes:
            continue
        if document_type:
            marker = document_type_markers.get(document_type.lower())
        else:
            marker = None
        parsed.partial_codes.append((code, marker))

    # "Nghị định 218": chỉ có số, xác định văn bản như số hiệu rút gọn
    for document_type, number in number_only_code_pattern.findall(text):
        marker = document_type_markers.get(document_type.lower())
        if (number, marker) not in parsed.partial_codes:
            parsed.partial_codes.append((number, marker))

    # Điều / Khoản / Điểm
    for diem, khoan, dieu in article_pattern.findall(text):
        article = ArticleReference(dieu=dieu, khoan=khoan or None, diem=diem or None)
        parsed.articles.append(article)

    # Tên văn bản: viết tắt / tên thông dụng trước
    alias_spans = []
    for match in alias_pattern.finditer(text):
        name = document_aliases[match.group(1).lower()]
        alias_spans.append((match.start(), match.end()))
        known_names = [document.name for document in parsed.documents]
        if name not in known_names:
            year = year_after(text, match.end())
            parsed.documents.append(DocumentMention(name=name, year=year, exact=True))

    # Sau đó đoạn chữ sau "Luật / Bộ luật / ..." (bỏ đoạn trùng vị trí với viết tắt đã nhận)
    for match in document_name_pattern.finditer(text):
        if overlaps_any(match.start(), match.end(), alias_spans):
            continue
        document_type = match.group(1)
        rest = re.sub(r"[,\s]+$", "", match.group(2).strip())
        name = f"{document_type[0].upper()}{document_type[1:].lower()} {rest}"
        if len(name.split()) >= 2:
            year = year_after(text, match.end())
            parsed.documents.append(DocumentMention(name=name, year=year))

    # Tỉnh / thành phố (quy về tên chuẩn)
    for match in province_pattern.finditer(text):
        province = match.group(1) or match.group(2)
        province = province_canonical_names.get(province, province)
        if province not in parsed.provinces:
            parsed.provinces.append(province)
    return parsed


def expand_query(query: str) -> Tuple[str, List[str]]:
    """Bổ sung thuật ngữ pháp lý cho cách nói đời thường (rule base: src/rules/legal_terms.py).
    Trả về (câu hỏi đã bổ sung, danh sách thuật ngữ); không đổi nếu không khớp mẫu nào."""
    terms = []
    lowered_query = query.lower()
    for pattern, legal_term in lay_to_legal_terms:
        if not pattern.search(query):
            continue
        if legal_term in terms:
            continue
        # Câu hỏi đã có sẵn thuật ngữ này
        if legal_term.lower() in lowered_query:
            continue
        terms.append(legal_term)

    if not terms:
        return query, []
    expanded_query = f"{query} ({'; '.join(terms)})"
    return expanded_query, terms


def complete_second_part(first: str, second: str) -> str:
    """Vế sau của câu so sánh thiếu ngữ cảnh ("mức phạt ... của xe máy và ô tô") -> mượn phần trước "của" của vế đầu."""
    if " của " not in first:
        return second
    if " của " in second:
        return second
    if question_word_pattern.search(second):
        return second
    if len(second.split()) >= len(first.split()):
        return second
    return first.rsplit(" của ", 1)[0] + " của " + second


def split_subqueries(query: str) -> List[str]:
    """Tách câu so sánh / câu nhiều vế thành câu hỏi con (rỗng nếu câu hỏi đơn)."""
    text = normalize_unicode(query).strip()

    # Câu so sánh: "So sánh A và B", "A khác B thế nào"
    for pattern in comparison_patterns:
        match = pattern.match(text)
        if not match:
            continue
        first = match.group(1).strip(" ,")
        second = match.group(2).strip(" ,")
        second = complete_second_part(first, second)
        if len(first.split()) >= 2 and len(second.split()) >= 2:
            return [first, second]

    # Câu nhiều vế nối bằng "và", mỗi vế đều là một câu hỏi đủ dài
    parts = multi_part_split_pattern.split(text)
    if len(parts) != 2:
        return []
    for part in parts:
        if not question_word_pattern.search(part):
            return []
        if len(part.split()) < 4:
            return []
    first = parts[0].strip(" ,?")
    second = parts[1].strip(" ,?")
    return [first, resolve_anaphora(second, first)]


def resolve_anaphora(second: str, first: str) -> str:
    """Vế sau dùng đại từ thay cho điều kiện / chủ thể của vế trước ("khi đó", "họ") -> thay bằng nội dung vế trước
    để câu hỏi con tự đứng được khi truy xuất / rerank riêng."""
    if condition_reference_pattern.search(second):
        condition = question_tail_pattern.sub(" ", first)
        condition = re.sub(r"\s+", " ", condition).strip()
        rest = condition_reference_pattern.sub("", second).strip()
        return f"{rest} khi {condition[0].lower()}{condition[1:]}"

    match = subject_reference_pattern.search(second)
    if match:
        subject = subject_end_pattern.split(first, maxsplit=1)[0]
        subject = subject[0].lower() + subject[1:]
        return second[: match.start()] + subject + second[match.end():]
    return second
