"""Gộp nhiều danh sách kết quả tìm kiếm bằng Weighted Reciprocal Rank Fusion (RRF)."""
from typing import List, Tuple

from src.retrieval import settings
from src.retrieval.query_parser import ParsedQuery


def prior_for(source: dict, parsed: ParsedQuery) -> float:
    """Hệ số ưu tiên (rule-based) theo hiệu lực / phạm vi / địa phương."""
    prior = settings.status_prior.get(source.get("tinh_trang_hieu_luc"), 0.9)
    if parsed.provinces:
        # Câu hỏi nhắc tỉnh: ưu tiên Điều có tiêu đề / nội dung nhắc tỉnh đó
        title_and_text = (source.get("title") or "") + " " + (source.get("text") or "")[:2000]
        for province in parsed.provinces:
            if province in title_and_text:
                prior *= settings.province_prior
                break
    elif source.get("pham_vi") == "Trung ương":
        prior *= settings.central_prior
    return prior


def fuse_ranked_lists(ranked_lists: List[Tuple[float, List[dict]]], parsed: ParsedQuery) -> List[dict]:
    """Weighted RRF: mỗi danh sách (trọng số, hits) cộng trọng số / (rrf_constant + thứ hạng) cho từng Điều,
    sau đó nhân hệ số ưu tiên. Trả về hits xếp theo điểm giảm dần, kèm khóa fusion_score."""
    scores = {}
    hits = {}
    for weight, ranked_hits in ranked_lists:
        for rank, hit in enumerate(ranked_hits, 1):
            hit_id = hit["_id"]
            scores[hit_id] = scores.get(hit_id, 0.0) + weight / (settings.rrf_constant + rank)
            if hit_id not in hits:
                hits[hit_id] = hit

    for hit_id, hit in hits.items():
        scores[hit_id] *= prior_for(hit["_source"], parsed)

    fused = []
    for hit_id in sorted(scores, key=scores.get, reverse=True):
        fused_hit = dict(hits[hit_id])
        fused_hit["fusion_score"] = scores[hit_id]
        fused.append(fused_hit)
    return fused
