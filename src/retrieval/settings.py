"""Tham số truy xuất. Các hàm truy xuất đọc tham số qua `settings.<tên>` lúc chạy."""

# Weighted Reciprocal Rank Fusion: điểm = trọng số / (rrf_constant + thứ hạng)
rrf_constant = 60

# Số ứng viên lấy từ mỗi nhánh tìm kiếm
knn_size = 50              # kNN toàn cục (câu gốc, câu đã bổ sung thuật ngữ)
bm25_size = 50             # BM25 trên nội dung Điều
scoped_size = 20           # kNN giới hạn trong văn bản được nhắc tới / theo câu hỏi con

# Trọng số của từng nhánh khi gộp RRF
weight_knn = 1.0
weight_bm25 = 0.1
weight_scoped = 1.0
weight_subquery = 0.7

# Hệ số ưu tiên (nhân vào điểm RRF)
status_prior = {"Còn hiệu lực": 1.0, "Hết hiệu lực một phần": 0.97}   # trạng thái khác: 0.9
central_prior = 1.05       # văn bản Trung ương khi câu hỏi không nhắc địa phương nào
province_prior = 1.25      # tiêu đề / nội dung có nhắc tỉnh, thành phố trong câu hỏi

# Bổ sung thuật ngữ pháp lý cho câu hỏi đời thường (src/rules/legal_terms.py)
expand_legal_terms = True

# Số hiệu rút gọn khớp nhiều văn bản: tiêu đề phải đạt tỉ lệ này của điểm khớp cao nhất mới được xét tiếp theo hiệu lực
short_code_title_ratio = 0.75
