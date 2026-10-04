from FlagEmbedding import FlagReranker
import torch
from src.config import RERANKER_MODEL_NAME

device = "cuda" if torch.cuda.is_available() else "cpu"
reranker = FlagReranker(RERANKER_MODEL_NAME, use_fp16=(device == "cuda"))

def rerank_results(query_text: str, search_hits: list, top_k: int = 5):
    if not search_hits:
        return []

    pairs = [[query_text, hit["_source"]["text"]] for hit in search_hits]
    scores = reranker.compute_score(pairs, normalize=True)

    if isinstance(scores, float):
        scores = [scores]

    reranked_hits = []
    for hit, score in zip(search_hits, scores):
        hit_copy = dict(hit)
        hit_copy["rerank_score"] = float(score)
        reranked_hits.append(hit_copy)

    reranked_hits.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked_hits[:top_k]