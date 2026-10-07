import re
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import torch
from src.config import ES_HOST, INDEX_NAME, EMBEDDING_MODEL_NAME

device = "cuda" if torch.cuda.is_available() else "cpu"
es = Elasticsearch(ES_HOST)

embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
embed_model.max_seq_length = 2048

# Trọng số BM25 theo từng trường metadata
FIELD_BOOSTS = {"text": 1.0, "title": 2.0, "so_ky_hieu": 3.0}
TITLE_PHRASE_BOOST = 3.0      # cụm từ trong query khớp nguyên cụm với title
SO_KY_HIEU_EXACT_BOOST = 10.0 # query có nhắc đúng số hiệu văn bản

# Bắt số_hiệu_văn_bản trong query
SO_KY_HIEU_RE = re.compile(r"\b\d{1,4}(?:/[0-9A-Za-zĐđ\-]+)+", re.UNICODE)

def extract_so_ky_hieu(query: str) -> list:
    codes = []
    for m in SO_KY_HIEU_RE.findall(query):
        # bỏ ngày tháng dạng 12/05/2024 (không có chữ cái)
        if re.search(r"[A-Za-zĐđ]", m):
            codes.append(m.strip("-/"))
    return list(dict.fromkeys(codes))

def build_text_query(query_text: str, text_boost: float) -> dict:
    fields = [f"{f}^{b}" for f, b in FIELD_BOOSTS.items()]
    should = [
        # BM25 trên nhiều trường: text + title + so_ky_hieu
        {"multi_match": {"query": query_text, "fields": fields,
                         "type": "best_fields", "tie_breaker": 0.3, "boost": text_boost}},
        # Thưởng thêm khi cụm từ khớp nguyên cụm với tiêu đề văn bản
        {"match_phrase": {"title": {"query": query_text, "boost": TITLE_PHRASE_BOOST * text_boost}}},
    ]
    # Thưởng mạnh khi người dùng nhắc đúng số hiệu (không phân biệt hoa thường)
    for code in extract_so_ky_hieu(query_text):
        should.append({"term": {"so_ky_hieu": {"value": code, "case_insensitive": True,
                                               "boost": SO_KY_HIEU_EXACT_BOOST * text_boost}}})
    return {"bool": {"should": should, "minimum_should_match": 1}}

def hybrid_search(query_text: str, top_k: int = 10, text_boost: float = 0.3, vector_boost: float = 0.7, filter_conditions: list = None):
    if filter_conditions is None:
        filter_conditions = []

    query_vector_np = embed_model.encode(query_text, normalize_embeddings=True, show_progress_bar=False)
    query_vector = [float(v) for v in query_vector_np]

    search_query = {
        "size": top_k,
        "query": {
            "bool": {
                "must": [build_text_query(query_text, text_boost)],
                "filter": filter_conditions,
            }
        },
        "knn": {
            "field": "vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": max(100, top_k * 10),
            "boost": vector_boost,
            "filter": filter_conditions,
        },
        "_source": [
            "chunk_id", "doc_id", "so_ky_hieu", "title",
            "partId", "partType", "text", "tinh_trang_hieu_luc", "ngay_ban_hanh"
        ],
    }
    return es.search(index=INDEX_NAME, body=search_query)