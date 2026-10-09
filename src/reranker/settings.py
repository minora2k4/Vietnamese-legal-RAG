"""Tham số rerank, đã chọn bằng benchmark (xem optimize.md). Đọc qua `settings.<tên>` lúc chạy để
eval/run_retrieval.py --set có thể ghi đè."""

# Số token tối đa của mỗi cặp (câu hỏi, tiêu đề + nội dung Điều)
rerank_max_length = 512

# Điều có điểm rerank dưới ngưỡng không đưa cho LLM (trừ Điều hỏi đích danh và Điều điểm cao nhất)
min_rerank_score = 0.2

# Khi chọn Điều cho từng vế câu hỏi: trừ điểm khớp cao nhất của Điều đó với các vế khác (chọn Điều đặc trưng cho vế)
subquery_overlap_penalty = 1.0
