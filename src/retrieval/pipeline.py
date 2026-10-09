"""retrieve(): toàn bộ quy trình truy xuất cho một câu hỏi.

1. Phân tích câu hỏi (số ký hiệu, Điều, tên văn bản, tỉnh), tách câu hỏi con, xác định văn bản được nhắc tới.
2. Các nhánh tìm kiếm: kNN câu gốc, BM25, kNN câu đã bổ sung thuật ngữ, kNN trong văn bản được nhắc tới,
   kNN theo từng câu hỏi con -> gộp bằng Weighted RRF -> loại Điều sai đối tượng.
3. Điều hỏi đích danh được tra thẳng và luôn có mặt; rerank top_search ứng viên; chọn top_rerank Điều cuối.
"""
import time
from typing import Optional

from src.reranker.rerank import score_pairs, select_final
from src.retrieval import settings
from src.retrieval.documents import resolve_documents
from src.retrieval.embedding import encode
from src.retrieval.fusion import fuse_ranked_lists
from src.retrieval.query_parser import ArticleReference, expand_query, parse_query, split_subqueries
from src.retrieval.search import bm25_search, knn_search, lookup_articles, without_status
from src.retrieval.subject_filter import find_subjects, subject_mismatch
from src.rules.questions import document_overview_pattern


def retrieve(query: str, top_search: int = 10, top_rerank: int = 3, filter_conditions: Optional[list] = None) -> dict:
    """Trả về {"candidates": hits đã rerank, "final": hits đưa cho LLM, "debug": thông tin phân tích, "timings": ms}."""
    start_time = time.perf_counter()
    filters = list(filter_conditions or [])

    # 1. Phân tích câu hỏi
    parsed = parse_query(query)
    subqueries = split_subqueries(query)
    documents = []
    if parsed.has_document_reference:
        documents = resolve_documents(parsed, query)

    # Rule-based: hỏi tổng quan một văn bản ("Nghị định X quy định về những nội dung gì?") -> ghim Điều 1
    asks_document_overview = document_overview_pattern.search(query) is not None
    if documents and not parsed.articles and asks_document_overview:
        parsed.articles.append(ArticleReference(dieu="1"))

    # Câu hỏi bổ sung thuật ngữ pháp lý: thêm một nhánh kNN và dùng để rerank (vẫn giữ nhánh kNN của câu gốc)
    if settings.expand_legal_terms:
        expanded_query, legal_terms = expand_query(query)
    else:
        expanded_query, legal_terms = query, []

    texts_to_encode = [query] + subqueries
    if legal_terms:
        texts_to_encode.append(expanded_query)
    vectors = encode(texts_to_encode)
    query_vector = vectors[0]
    subquery_vectors = vectors[1:1 + len(subqueries)]

    # 2. Các nhánh tìm kiếm: (trọng số RRF, danh sách hit)
    ranked_lists = []
    ranked_lists.append((settings.weight_knn, knn_search(query_vector, settings.knn_size, filters)))
    if settings.weight_bm25 > 0:
        ranked_lists.append((settings.weight_bm25, bm25_search(query, parsed, settings.bm25_size, filters)))
    if legal_terms:
        expanded_vector = vectors[-1]
        ranked_lists.append((settings.weight_knn, knn_search(expanded_vector, settings.knn_size, filters)))

    # Nhánh trong phạm vi văn bản được hỏi đích danh: không lọc theo hiệu lực
    scoped_filters = filters
    if documents:
        document_ids = [document.doc_id for document in documents]
        scoped_filters = without_status(filters) + [{"terms": {"doc_id": document_ids}}]
        ranked_lists.append((settings.weight_scoped, knn_search(query_vector, settings.scoped_size, scoped_filters)))
    for subquery_vector in subquery_vectors:
        subquery_hits = knn_search(subquery_vector, settings.scoped_size, scoped_filters)
        ranked_lists.append((settings.weight_subquery, subquery_hits))

    # Gộp RRF rồi loại Điều dành cho đối tượng khác với câu hỏi
    query_subjects = find_subjects(query)
    fused = []
    for hit in fuse_ranked_lists(ranked_lists, parsed):
        if subject_mismatch(query_subjects, hit["_source"]):
            continue
        fused.append(hit)

    # 3. Điều hỏi đích danh luôn nằm trong ứng viên (không lọc hiệu lực), phần còn lại lấy theo thứ hạng RRF
    pinned = lookup_articles(parsed, documents, without_status(filters))
    pinned_ids = {hit["_id"] for hit in pinned}
    remaining_slots = max(top_search - len(pinned), 0)
    other_hits = []
    for hit in fused:
        if hit["_id"] not in pinned_ids:
            other_hits.append(hit)
    candidates = pinned + other_hits[:remaining_slots]

    # Rerank và chọn các Điều cuối cùng
    rerank_start_time = time.perf_counter()
    scores = score_pairs(expanded_query, candidates)
    for hit, score in zip(candidates, scores):
        hit["rerank_score"] = score
    final = select_final(candidates, pinned_ids, subqueries, top_rerank)

    # Đánh dấu trích lục thuộc văn bản được hỏi đích danh (prompt cho phép dùng kèm nhãn hiệu lực)
    named_document_ids = {document.doc_id for document in documents}
    for hit in final:
        hit["asked"] = hit["_source"].get("doc_id") in named_document_ids
    end_time = time.perf_counter()

    # Khóa của debug / timings giữ nguyên để tương thích các file kết quả cũ trong eval/results và API
    debug = {
        "codes": parsed.codes,
        "partial_codes": parsed.partial_codes,
        "articles": [article.dieu for article in parsed.articles],
        "docs": [f"{document.so_ky_hieu} ({document.status})" for document in documents],
        "provinces": parsed.provinces,
        "subqueries": subqueries,
        "legal_terms": legal_terms,
        "subjects": {group: sorted(names) for group, names in query_subjects.items()},
        "pinned": len(pinned),
    }
    timings = {
        "search_ms": int((rerank_start_time - start_time) * 1000),
        "rerank_ms": int((end_time - rerank_start_time) * 1000),
    }
    return {"candidates": candidates, "final": final, "debug": debug, "timings": timings}
