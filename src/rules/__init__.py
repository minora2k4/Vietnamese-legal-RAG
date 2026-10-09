"""RULE BASE: tri thức viết tay (regex, từ điển) về văn bản pháp luật và cách hỏi tiếng Việt.

Mọi luật phụ thuộc ngôn ngữ / lĩnh vực nằm trong package này. Code xử lý (src/retrieval, src/reranker,
src/generation) chỉ áp dụng các luật ở đây, không tự chứa luật riêng.
Thêm / sửa luật: chỉ sửa file trong src/rules/, sau đó chạy lại benchmark trong eval/.

- documents.py   : số ký hiệu, Điều/Khoản/Điểm, tên và viết tắt văn bản, cấu trúc tiêu đề, nhãn hiệu lực
- places.py      : tỉnh / thành phố
- questions.py   : câu so sánh, câu nhiều vế, đại từ thay thế, câu hỏi tổng quan về một văn bản
- legal_terms.py : cách nói đời thường -> thuật ngữ pháp lý
- subjects.py    : nhóm đối tượng áp dụng loại trừ nhau (ví dụ loại phương tiện giao thông)
- answers.py     : mẫu kiểm tra câu trả lời của LLM
"""
