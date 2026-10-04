from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import torch
from src.config import ES_HOST, INDEX_NAME, EMBEDDING_MODEL_NAME

device = "cuda" if torch.cuda.is_available() else "cpu"
es = Elasticsearch(ES_HOST)

# Tải model embedding khi khởi động
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
embed_model.max_seq_length = 2048

def hybrid_search(query_text: str, top_k: int = 10, text_boost: float = 0.3, vector_boost: float = 0.7, filter_conditions: list = None):
    if filter_conditions is None:
        filter_conditions = []

    query_vector_np = embed_model.encode(query_text, normalize_embeddings=True, show_progress_bar=False)
    query_vector = [float(v) for v in query_vector_np]

    search_query = {
        "size": top_k,
        "query": {
            "bool": {
                "must": [{"match": {"text": {"query": query_text, "boost": text_boost}}}],
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