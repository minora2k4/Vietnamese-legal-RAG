"""Module RERANK: chấm lại các Điều ứng viên bằng cross-encoder và chọn các Điều cuối cùng đưa cho LLM.

- settings.py : tham số rerank (độ dài tối đa, ngưỡng điểm, mức trừ điểm khi chọn theo câu hỏi con)
- model.py    : model cross-encoder BGE (tải lúc import, dùng GPU nếu có)
- rerank.py   : score_pairs() chấm điểm, select_final() chọn Điều cuối
"""
