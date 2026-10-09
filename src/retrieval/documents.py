"""Xác định văn bản được nhắc tới trong câu hỏi (số ký hiệu đầy đủ / rút gọn / chỉ có số, tên văn bản) -> doc_id."""
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.config import index_name
from src.retrieval import settings
from src.retrieval.elasticsearch_client import elasticsearch_client
from src.retrieval.query_parser import DocumentMention, ParsedQuery
from src.retrieval.text_normalization import normalize_code, normalize_name
from src.rules.documents import document_preference_key, document_type_of, title_name_words


@dataclass
class DocumentInfo:
    doc_id: str
    so_ky_hieu: str
    title: str
    status: str


def search_documents(query: dict, size: int = 30) -> List[dict]:
    """Tìm văn bản (mỗi doc_id một kết quả), trả về _source kèm điểm khớp _score."""
    body = {
        "size": size,
        "query": query,
        "collapse": {"field": "doc_id"},
        "_source": ["doc_id", "so_ky_hieu", "title", "tinh_trang_hieu_luc", "ngay_ban_hanh", "pham_vi"],
    }
    response = elasticsearch_client.search(index=index_name, body=body)
    sources = []
    for hit in response["hits"]["hits"]:
        source = dict(hit["_source"])
        source["_score"] = hit.get("_score") or 0.0
        sources.append(source)
    return sources


def common_prefix_length(first: List[str], second: List[str]) -> int:
    """Số từ trùng nhau tính từ đầu của hai danh sách từ."""
    length = 0
    for first_word, second_word in zip(first, second):
        if first_word != second_word:
            break
        length += 1
    return length


def name_match_score(mention: DocumentMention, mention_words: List[str], source: dict) -> Optional[float]:
    """Mức khớp giữa tên văn bản trong câu hỏi và tiêu đề văn bản trong ES (None nếu không khớp)."""
    title_words = normalize_name(source.get("title") or "").split()
    name_words = title_name_words(title_words)
    if len(name_words) < 2:
        return None
    shared = common_prefix_length(mention_words, name_words)
    # Câu hỏi chứa trọn tên văn bản
    if shared == len(name_words):
        return shared
    # Người dùng chỉ viết phần đầu của tên (không áp dụng cho tên chuẩn lấy từ bảng viết tắt)
    if not mention.exact and shared >= 3 and shared == len(mention_words):
        return shared - 0.5
    return None


def resolve_documents(parsed: ParsedQuery, query: str = "", max_documents: int = 2) -> List[DocumentInfo]:
    """Rule-based: số ký hiệu / tên văn bản trong câu hỏi -> doc_id.
    - Số ký hiệu đầy đủ: văn bản trùng chính xác đứng trước văn bản chỉ nhắc số đó trong tiêu đề (sửa đổi, hướng dẫn).
    - Số hiệu rút gọn / chỉ có số khớp nhiều văn bản: ưu tiên văn bản có tiêu đề khớp nội dung câu hỏi rõ hơn hẳn.
    - Tên văn bản: so theo tiền tố với phần tên trong tiêu đề ES.
    Nhiều văn bản cùng khớp thì xếp theo document_preference_key (rule base); mỗi tham chiếu lấy tối đa max_documents."""
    found: Dict[str, DocumentInfo] = {}

    def add(sources):
        for source in sources[:max_documents]:
            if source["doc_id"] in found:
                continue
            found[source["doc_id"]] = DocumentInfo(doc_id=source["doc_id"], so_ky_hieu=source.get("so_ky_hieu"),
                                                   title=source.get("title"), status=source.get("tinh_trang_hieu_luc"))

    # Số ký hiệu đầy đủ: trùng so_ky_hieu hoặc tiêu đề có nhắc số ký hiệu (văn bản hợp nhất VBHN)
    if parsed.codes:
        should = [{"terms": {"so_ky_hieu": parsed.codes}}]
        for code in parsed.codes:
            should.append({"match_phrase": {"title": code}})
        sources = search_documents({"bool": {"should": should, "minimum_should_match": 1}})

        exact_codes = set()
        for code in parsed.codes:
            exact_codes.add(normalize_code(code))

        def exact_code_first(source):
            is_other_document = normalize_code(source.get("so_ky_hieu")) not in exact_codes
            return (is_other_document, document_preference_key(source, None))

        add(sorted(sources, key=exact_code_first))

    # Số hiệu rút gọn ("168/2024") hoặc chỉ có số ("218"), kèm loại văn bản nếu câu hỏi có nêu
    for code, marker in parsed.partial_codes:
        # Loại văn bản phải có trong số ký hiệu đầy đủ ("Thông tư 02/2021" -> "02/2021/*TT*")
        if marker:
            code_match = {"wildcard": {"so_ky_hieu": {"value": f"{code}/*{marker}*", "case_insensitive": True}}}
        else:
            code_match = {"prefix": {"so_ky_hieu": code + "/"}}
        candidate_filter = {"bool": {"should": [code_match, {"match_phrase": {"title": code}}],
                                     "minimum_should_match": 1}}
        # Điểm khớp giữa tiêu đề văn bản và câu hỏi, dùng để chọn khi nhiều văn bản cùng số hiệu
        if query:
            title_relevance = [{"match": {"title": query}}]
        else:
            title_relevance = []
        sources = search_documents({"bool": {"filter": [candidate_filter], "should": title_relevance}})

        if marker:
            sources_with_marker = []
            for source in sources:
                if marker in str(source.get("so_ky_hieu")).upper():
                    sources_with_marker.append(source)
            sources = sources_with_marker

        best_score = 0.0
        if sources:
            best_score = max(source["_score"] for source in sources)

        # Văn bản có số ký hiệu bắt đầu bằng số hiệu được hỏi và tiêu đề khớp câu hỏi rõ hơn hẳn đứng trước
        def short_code_order(source):
            starts_with_code = normalize_code(source.get("so_ky_hieu")).startswith(code + "/")
            weak_title_match = source["_score"] < settings.short_code_title_ratio * best_score
            return (not starts_with_code, weak_title_match, document_preference_key(source, None))

        add(sorted(sources, key=short_code_order))

    # Tên văn bản ("Luật Hôn nhân và gia đình 2014", "BLHS")
    for mention in parsed.documents:
        mention_words = normalize_name(mention.name).split()
        title_query = {"bool": {
            "must": [{"match": {"title": {"query": mention.name, "minimum_should_match": "60%"}}}],
            "filter": [{"prefix": {"title.keyword": {"value": document_type_of(mention_words),
                                                     "case_insensitive": True}}}],
        }}
        # Giữ các văn bản có mức khớp tên cao nhất
        best_score = 0.0
        best_sources = []
        for source in search_documents(title_query, size=50):
            score = name_match_score(mention, mention_words, source)
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_sources = [source]
            elif score == best_score:
                best_sources.append(source)

        def preference_for_mention(source):
            return document_preference_key(source, mention.year)

        add(sorted(best_sources, key=preference_for_mention))
    return list(found.values())
