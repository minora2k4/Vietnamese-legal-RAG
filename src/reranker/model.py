"""Model cross-encoder BGE reranker (tải lúc import; fp16 trên GPU)."""
import torch
from FlagEmbedding import FlagReranker

from src.config import reranker_model_name

device = "cuda" if torch.cuda.is_available() else "cpu"

reranker_model = FlagReranker(reranker_model_name, use_fp16=(device == "cuda"))
