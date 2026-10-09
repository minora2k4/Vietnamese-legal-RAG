"""Các nhánh tìm kiếm Điều luật trong Elasticsearch: kNN, BM25, tra thẳng Điều được hỏi đích danh.

Không cộng điểm BM25 với điểm kNN trong cùng một truy vấn (điểm BM25 10–50 lấn át cosine ≤ 1): mỗi nhánh là một
truy vấn riêng, kết quả được gộp bằng thứ hạng (src/retrieval/fusion.py)."""
from typing import List

from src.config import index_name
from src.retrieval.documents import DocumentInfo
from src.retrieval.elasticsearch_client import elasticsearch_client
from src.retrieval.query_parser import ParsedQuery

# Các trường lấy về cho mỗi Điều
source_fields = ["chunk_id", "doc_id", "so_ky_hieu", "title", "partId", "partType", "khoanId",
                 "text", "tinh_trang_hieu_luc", "ngay_ban_hanh", "ngay_co_hieu_luc", "ngay_het_hieu_luc", "pham_vi"]


def without_status(filters: list) -> list:
    """Bỏ điều kiện hiệu lực khỏi bộ lọc: văn bản được hỏi đích danh vẫn được truy xuất dù đã hết / chưa có hiệu lực
    (LLM được báo tình trạng hiệu lực qua nhãn của trích lục)."""
    kept_conditions = []
    for condition in filters:
        if "tinh_trang_hieu_luc" in str(condition):
            continue
        kept_conditions.append(condition)
    return kept_conditions


def search_chunks(body: dict) -> List[dict]:
    """Chạy một truy vấn ES, trả về danh sách hit (mỗi hit là một Điều)."""
    body.setdefault("_source", source_fields)
    response = elasticsearch_client.search(index=index_name, body=body)
    return response["hits"]["hits"]


def knn_search(vector: List[float], size: int, filters: list) -> List[dict]:
    """Tìm theo vector (approximate kNN), lấy size kết quả trong num_candidates ứng viên."""
    knn = {
        "field": "vector",
        "query_vector": vector,
        "k": size,
        "num_candidates": max(200, size * 10),
        "filter": filters,
    }
    return search_chunks({"size": size, "knn": knn})


def bm25_search(query: str, parsed: ParsedQuery, size: int, filters: list) -> List[dict]:
    """Tìm theo từ khóa trên nội dung Điều; cộng thêm điểm khi trùng số ký hiệu / tiêu đề có nhắc tỉnh trong câu hỏi."""
    should = [
        {"match": {"text": {"query": query, "minimum_should_match": "60%"}}},
        {"match_phrase": {"text": {"query": query, "slop": 2, "boost": 2.0}}},
    ]
    for code in parsed.codes:
        should.append({"term": {"so_ky_hieu": {"value": code, "boost": 5.0}}})
    for province in parsed.provinces:
        should.append({"match_phrase": {"title": {"query": province, "boost": 3.0}}})
    query_body = {"bool": {"should": should, "minimum_should_match": 1, "filter": filters}}
    return search_chunks({"size": size, "query": query_body})


def lookup_articles(parsed: ParsedQuery, documents: List[DocumentInfo], filters: list) -> List[dict]:
    """Lấy thẳng các Điều được hỏi đích danh trong các văn bản đã xác định (xếp theo thứ tự văn bản, rồi thứ tự Điều)."""
    if not parsed.articles or not documents:
        return []

    article_numbers = []
    for article in parsed.articles:
        if article.dieu not in article_numbers:
            article_numbers.append(article.dieu)
    document_ids = [document.doc_id for document in documents]

    conditions = filters + [{"terms": {"doc_id": document_ids}}, {"terms": {"partId": article_numbers}}]
    hits = search_chunks({"size": 10 * len(article_numbers), "query": {"bool": {"filter": conditions}}})

    document_order = {}
    for index, document in enumerate(documents):
        document_order[document.doc_id] = index

    def article_order(hit):
        source = hit["_source"]
        return (document_order.get(source["doc_id"], 99), article_numbers.index(source["partId"]))

    return sorted(hits, key=article_order)
