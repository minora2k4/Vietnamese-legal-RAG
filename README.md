# Vietnamese Legal RAG System

Hệ thống Trợ lý Pháp luật thông minh ứng dụng kiến trúc **Retrieval-Augmented Generation (RAG)** kết hợp **Hybrid Search** và **LLM**, giúp tra cứu, tổng hợp và trả lời các thắc mắc pháp lý chuẩn xác dựa trên cơ sở dữ liệu Văn bản Quản lý Nhà nước & Luật Việt Nam.

## Dataset: 
* Bộ dataset (`th1nhng0/vietnamese-legal-documents`) 170k văn bản quy phạm pháp luật Việt Nam
---

## Tính năng nổi bật
* **Hybrid Search (Vector Search + Keyword Search):** Kết hợp kNN Dense Vector (`AITeamVN/Vietnamese_Embedding_v2`) và BM25 Keyword Search trên Elasticsearch để tối ưu khả năng truy vấn điều khoản pháp luật.
* **Semantic Reranking:** Sử dụng mô hình `BAAI/bge-reranker-v2-m3` để lọc điểm số liên quan, loại bỏ các văn bản nhiễu trước khi đưa vào Context.
* **LLM Inference:** Tự host LLM Qwen (`Qwen/Qwen3.5-9B`) qua API vLLM / OpenAI-compatible endpoint bằng 2 GPU Tesla T4 (16x2 GB VRAM).
* **Loại bỏ nhiễu ngữ cảnh (Noise Filtering):** Rào Prompt & Threshold Reranker chặt chẽ, chỉ trích dẫn các văn bản có nội dung trực tiếp giải quyết câu hỏi.
* **FastAPI Backend & Web UI:** RESTful API tối ưu tốc độ phản hồi, hỗ trợ streaming kết quả và xử lý mượt mà các tĩnh tài nguyên.

---

## Kiến trúc Hệ thống (System Architecture)

<!-- PLACEHOLDER FOR PIPELINE DIAGRAM -->
<img width="1373" height="604" alt="{F72536EC-D9A4-49B8-83F3-FFC56B4BC774}" src="https://github.com/user-attachments/assets/5ddf7964-fb50-437b-bd19-b881eedfae93" />

*Hình 1: Luồng xử lý dữ liệu từ truy vấn người dùng, Hybrid Search, Reranking đến sinh câu trả lời bằng LLM.*

### Luồng xử lý chi tiết (Data Flow)
1. **User Query:** Người dùng gửi câu hỏi qua Web UI / API.
2. **Hybrid Retrieval:** Elasticsearch thực hiện tìm kiếm kết hợp Dense Embedding & Sparse BM25.
3. **Reranking & Filtering:** BGE Reranker chấm lại điểm relevance score, loại bỏ tài liệu dưới ngưỡng (Score Threshold).
4. **Prompt Construction:** `src/prompt.py` đóng gói danh sách căn cứ hợp lệ kèm câu hỏi.
5. **LLM Generation:** LLM xử lý context và sinh câu trả lời kèm trích dẫn số hiệu văn bản/điều khoản cụ thể.

---

## Giao diện Ứng dụng (User Interface)

<!-- PLACEHOLDER FOR UI SCREENSHOT -->
<img width="1914" height="910" alt="{FE63F0FD-0AA6-41D1-9BE3-E1759ED7289D}" src="https://github.com/user-attachments/assets/c36bccc9-92f1-4cd4-bc09-1aa900db9f8c" />
*Hình 2: Giao diện tra cứu pháp luật và hiển thị câu trả lời kèm Căn cứ pháp lý chi tiết.*

---

## Cấu trúc Thư mục Dự án

```text
legal-graph-rag/
├── src/
│   ├── __init__.py
│   ├── config.py                # Cấu hình biến môi trường, Elasticsearch, LLM, Models
│   ├── llm_service.py           # Xử lý kết nối LLM và sinh chuỗi trả lời
│   ├── prompt.py                # Định nghĩa System Prompt và hàm build_user_message
│   ├── retriever.py             # Module tìm kiếm Hybrid Search & Reranking
│   └── utils.py                 # Các hàm tiện ích hỗ trợ
├── ui/                          # Giao diện UI
├── docker-compose.yml           # Khởi chạy Elasticsearch & Kibana
├── main.py                      # Khởi chạy ứng dụng FastAPI
├── vLLM_self_host_kaggle.ipynb  # Upload notebook lên Kaggle để tự Host model LLM
├── start.sh                     # Script khởi động tự động môi trường & dịch vụ
└── requirements.txt             # Danh sách thư viện Python
