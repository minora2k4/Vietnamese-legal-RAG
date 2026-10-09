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
4. **Prompt Construction:** `src/generation/prompt.py` đóng gói danh sách căn cứ hợp lệ kèm câu hỏi.
5. **LLM Generation:** LLM xử lý context và sinh câu trả lời kèm trích dẫn số hiệu văn bản/điều khoản cụ thể.

---

## Tốc độ xử lý

Đo ngày 2026-10-09 trên cấu hình mặc định (`top_search=10`, `top_rerank=3`):

- **Truy xuất + rerank:** laptop RTX 3050 Ti 4 GB; Elasticsearch chạy trong Docker (VM 3,65 GB RAM), đã tắt Kibana.
- **LLM:** Qwen3.5-9B trên vLLM, Kaggle 2×T4, gọi qua Cloudflare tunnel; mỗi luồng sinh khoảng 10 token/s.

**Mỗi câu hỏi** (E2E qua `POST /api/chat`, 350 câu của `eval/legal_bench_200.json` + `eval/code_bench.json`, gửi 3 câu song song):

| Bước | Trung vị | Trung bình | p90 |
|---|---|---|---|
| Truy xuất: phân tích câu hỏi, embedding, kNN / BM25, RRF | 0,6 s | 0,7 s | 0,9 s |
| Rerank (BGE reranker, 10 ứng viên) | 0,7 s | 0,7 s | 0,7 s |
| LLM: sinh câu trả lời| 54,6 s | 55,8 s | 74,4 s |
| **Tổng** | **56,0 s** | **57,3 s** | **76,2 s** |

- Truy xuất + rerank chạy riêng (không gọi LLM, mỗi lần 1 câu, `eval/run_retrieval.py`): trung vị 1,2–1,5 s/câu, p90 1,6–2,7 s.
- Truy vấn đầu tiên, hoặc khi vector chưa nằm trong cache của ES, có thể mất 4–10 s cho bước truy xuất. Nếu bật Kibana, bước truy xuất chậm khoảng gấp đôi.
- LLM chiếm khoảng 97% thời gian. Câu trả lời dài trung vị khoảng 1.350 ký tự.

**Nhiều câu hỏi song song** (3 câu cùng lúc; truy xuất chạy tuần tự trên GPU, các lời gọi LLM chạy song song nhờ vLLM batching):

| Lượt đo | Số câu | Tổng thời gian | Thông lượng |
|---|---|---|---|
| `legal_bench_200` | 200 | 64 phút | 19,2 s/câu (~3,1 câu/phút) |
| `code_bench` | 150 | 46 phút | 18,4 s/câu (~3,3 câu/phút) |

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
│   ├── config.py                    # Biến môi trường (.env), index Elasticsearch, tên các model
│   ├── rules/                       # Rule base dùng chung: regex, từ điển (số ký hiệu, viết tắt, tỉnh, thuật ngữ...)
│   ├── retrieval/                   # Truy xuất
│   │   ├── settings.py              # Tham số truy xuất (trọng số RRF, số ứng viên, hệ số ưu tiên)
│   │   ├── elasticsearch_client.py  # Kết nối Elasticsearch
│   │   ├── embedding.py             # Model embedding câu hỏi
│   │   ├── text_normalization.py    # Chuẩn hóa chuỗi để so khớp
│   │   ├── query_parser.py          # Phân tích câu hỏi, tách câu hỏi con, bổ sung thuật ngữ
│   │   ├── documents.py             # Xác định văn bản được nhắc tới -> doc_id
│   │   ├── search.py                # Các nhánh tìm kiếm: kNN, BM25, tra thẳng Điều
│   │   ├── fusion.py                # Gộp kết quả bằng Weighted RRF
│   │   ├── subject_filter.py        # Loại Điều sai đối tượng
│   │   └── pipeline.py              # retrieve(): toàn bộ quy trình truy xuất + rerank
│   ├── reranker/                    # Rerank
│   │   ├── settings.py              # Tham số rerank
│   │   ├── model.py                 # Model cross-encoder BGE
│   │   └── rerank.py                # Chấm điểm, chọn các Điều cuối cùng
│   └── generation/                  # Sinh câu trả lời
│       ├── prompt.py                # System prompt, user message
│       ├── llm_client.py            # Gọi LLM (vLLM, API tương thích OpenAI)
│       ├── answer_check.py          # Kiểm tra số tiền / số Điều có căn cứ
│       └── assistant.py             # ask_legal_assistant(): prompt -> LLM -> kiểm tra
├── ui/                              # Giao diện web
├── docker-compose.yml               # Khởi chạy Elasticsearch & Kibana
├── main.py                          # API FastAPI
├── vLLM_self_host_kaggle.ipynb      # Upload notebook lên Kaggle để tự host model LLM
├── start.sh                         # Script khởi động môi trường & dịch vụ
└── requirements.txt                 # Danh sách thư viện Python
