"""Chấm điểm (câu hỏi, Điều) bằng cross-encoder và chọn các Điều cuối cùng đưa cho LLM."""
from typing import List

from src.reranker import settings
from src.reranker.model import reranker_model


def score_pairs(query: str, hits: List[dict]) -> List[float]:
    """Chấm (câu hỏi, tiêu đề văn bản + nội dung Điều), điểm đã chuẩn hóa về 0–1. Tiêu đề cho reranker biết Điều
    thuộc văn bản nào (Bộ luật hay quyết định của một tỉnh)."""
    if not hits:
        return []
    pairs = []
    for hit in hits:
        source = hit["_source"]
        passage = f"{source.get('title') or ''}\n{source.get('text') or ''}"
        pairs.append([query, passage])
    scores = reranker_model.compute_score(pairs, normalize=True, max_length=settings.rerank_max_length)
    # Một cặp duy nhất: model trả về một số thay vì danh sách
    if isinstance(scores, float):
        return [float(scores)]
    return [float(score) for score in scores]


def best_scored(hits: List[dict]) -> dict:
    """Hit có điểm rerank cao nhất (bằng điểm thì lấy hit đứng trước)."""
    best_hit = hits[0]
    for hit in hits[1:]:
        if hit["rerank_score"] > best_hit["rerank_score"]:
            best_hit = hit
    return best_hit


def distinctiveness(index: int, current: int, subquery_scores: List[List[float]], candidates: List[dict]) -> float:
    """Mức đặc trưng của ứng viên index cho vế câu hỏi current:
    điểm theo vế này + điểm rerank chung - mức trừ * điểm cao nhất của ứng viên đó ở các vế khác."""
    other_scores = []
    for other in range(len(subquery_scores)):
        if other != current:
            other_scores.append(subquery_scores[other][index])
    best_other_score = 0.0
    if other_scores:
        best_other_score = max(other_scores)
    current_score = subquery_scores[current][index]
    overall_score = candidates[index]["rerank_score"]
    return current_score + overall_score - settings.subquery_overlap_penalty * best_other_score


def select_final(candidates: List[dict], pinned_ids: set, subqueries: List[str], top_rerank: int) -> List[dict]:
    """Chọn tối đa top_rerank Điều theo thứ tự:
    1. Điều được hỏi đích danh (pinned_ids);
    2. Điều có điểm rerank cao nhất;
    3. với mỗi vế câu hỏi: Điều đặc trưng nhất cho vế đó (xem distinctiveness);
    4. phần còn lại theo điểm rerank chung.
    Bước 3, 4 bỏ Điều dưới min_rerank_score. Kết quả: Điều hỏi đích danh trước, sau đó theo điểm giảm dần."""
    chosen = []
    chosen_ids = set()

    def take(hit, force=False):
        if hit["_id"] in chosen_ids:
            return
        if len(chosen) >= top_rerank:
            return
        if force or hit["rerank_score"] >= settings.min_rerank_score:
            chosen.append(hit)
            chosen_ids.add(hit["_id"])

    # 1. Điều được hỏi đích danh
    for hit in candidates:
        if hit["_id"] in pinned_ids:
            take(hit, force=True)

    # 2. Điều có điểm cao nhất
    if candidates:
        take(best_scored(candidates), force=True)

    # 3. Mỗi vế câu hỏi một Điều đặc trưng cho vế đó
    if subqueries and candidates:
        subquery_scores = []
        for subquery in subqueries:
            subquery_scores.append(score_pairs(subquery, candidates))
        for current in range(len(subqueries)):
            free_indexes = []
            for index, hit in enumerate(candidates):
                if hit["_id"] not in chosen_ids:
                    free_indexes.append(index)
            if not free_indexes:
                continue
            best_index = free_indexes[0]
            best_value = distinctiveness(best_index, current, subquery_scores, candidates)
            for index in free_indexes[1:]:
                value = distinctiveness(index, current, subquery_scores, candidates)
                if value > best_value:
                    best_index = index
                    best_value = value
            take(candidates[best_index])

    # 4. Phần còn lại theo điểm rerank
    def rerank_score_of(hit):
        return hit["rerank_score"]

    for hit in sorted(candidates, key=rerank_score_of, reverse=True):
        take(hit)

    # Điều hỏi đích danh đứng trước, sau đó theo điểm giảm dần
    def final_order(hit):
        is_not_pinned = hit["_id"] not in pinned_ids
        return (is_not_pinned, -hit["rerank_score"])

    return sorted(chosen, key=final_order)
