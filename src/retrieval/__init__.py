"""Module TRUY XUẤT: từ câu hỏi -> các Điều luật ứng viên (trước và sau rerank).

- settings.py             : tham số truy xuất (trọng số RRF, số ứng viên, hệ số ưu tiên)
- elasticsearch_client.py : kết nối Elasticsearch
- embedding.py            : model embedding câu hỏi
- text_normalization.py   : chuẩn hóa chuỗi để so khớp (unicode, tên văn bản, số ký hiệu)
- query_parser.py         : phân tích câu hỏi (số ký hiệu, Điều, tên văn bản, tỉnh), tách câu hỏi con, bổ sung thuật ngữ
- documents.py            : xác định văn bản được nhắc tới trong câu hỏi -> doc_id
- search.py               : các nhánh tìm kiếm trong ES (kNN, BM25, tra thẳng Điều)
- fusion.py               : gộp các danh sách kết quả bằng Weighted RRF
- subject_filter.py       : loại Điều dành cho đối tượng khác với câu hỏi
- pipeline.py             : retrieve() = toàn bộ quy trình truy xuất + rerank

Không import gì ở đây để code chỉ dùng phần phân tích câu hỏi (query_parser) không phải tải model.
"""
