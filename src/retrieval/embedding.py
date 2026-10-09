"""Model embedding câu hỏi (tải lúc import, dùng GPU nếu có).

Câu hỏi được encode KHÔNG có tiền tố; các đoạn văn bản trong ES đã được index với tiền tố "passage: ".
"""
from typing import List

import torch
from sentence_transformers import SentenceTransformer

from src.config import embedding_model_name

device = "cuda" if torch.cuda.is_available() else "cpu"

embedding_model = SentenceTransformer(embedding_model_name, device=device)
embedding_model.max_seq_length = 2048


def encode(texts: List[str]) -> List[List[float]]:
    """Encode nhiều câu một lượt -> vector đã chuẩn hóa (list float để gửi cho ES)."""
    vectors = embedding_model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    query_vectors = []
    for vector in vectors:
        query_vectors.append([float(value) for value in vector])
    return query_vectors
