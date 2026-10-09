"""API FastAPI + giao diện web tĩnh (ui/).

POST /api/chat: câu hỏi -> truy xuất + rerank (src/retrieval) -> LLM (src/generation) -> câu trả lời kèm căn cứ.
Tên các trường của request / response là giao kèo với ui/app.js, không đổi tùy tiện.
"""
import threading
import time
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.generation.assistant import ask_legal_assistant
from src.retrieval.pipeline import retrieve

app = FastAPI(title="Vietnamese Legal RAG API", version="1.1.0")
app.mount("/ui", StaticFiles(directory="ui"), name="ui")
app.mount("/ui/", StaticFiles(directory="ui"), name="ui")

# Lựa chọn hiệu lực trên UI -> giá trị thực tế của trường tinh_trang_hieu_luc trong ES (None = không lọc).
# "dang_ap_dung" là mặc định: các bộ luật lớn (Hình sự, Lao động, Tố tụng...) đều mang nhãn "Hết hiệu lực một phần"
# (chỉ bị sửa đổi vài điều), lọc riêng "Còn hiệu lực" sẽ loại mất chúng.
status_filter_values = {
    "dang_ap_dung": ["Còn hiệu lực", "Hết hiệu lực một phần"],
    "con_hieu_luc": ["Còn hiệu lực"],
    "het_mot_phan": ["Hết hiệu lực một phần"],
    "all": None,
}
date_format = "yyyy-MM-dd"  # định dạng ngày dùng trong điều kiện lọc ngay_ban_hanh gửi cho ES


class Filters(BaseModel):
    status: str = "dang_ap_dung"
    year_from: Optional[int] = Field(None, ge=1945, le=2100)
    year_to: Optional[int] = Field(None, ge=1945, le=2100)
    so_ky_hieu: Optional[str] = Field(None, max_length=100)


class ChatRequest(BaseModel):
    query: str = Field(..., max_length=1000)
    top_search: int = Field(10, ge=3, le=50)    # số ứng viên đưa vào rerank
    top_rerank: int = Field(3, ge=1, le=10)     # số Điều đưa cho LLM
    filters: Filters = Filters()


class SourceDocument(BaseModel):
    doc_id: Optional[str] = None
    title: str
    so_ky_hieu: str
    partId: str
    tinh_trang_hieu_luc: str
    ngay_ban_hanh: Optional[str] = None
    rerank_score: float
    text: str


class Timings(BaseModel):
    search_ms: int
    rerank_ms: int
    llm_ms: int
    total_ms: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    timings: Timings


def elapsed_milliseconds(start: float, end: float) -> int:
    return int((end - start) * 1000)


def build_filters(filters: Filters) -> list:
    """Bộ lọc trên UI -> danh sách điều kiện filter của ES."""
    conditions = []
    status_values = status_filter_values.get(filters.status, status_filter_values["dang_ap_dung"])
    if status_values:
        conditions.append({"terms": {"tinh_trang_hieu_luc": status_values}})
    date_range = {}
    if filters.year_from:
        date_range["gte"] = f"{filters.year_from}-01-01"
    if filters.year_to:
        date_range["lte"] = f"{filters.year_to}-12-31"
    if date_range:
        conditions.append({"range": {"ngay_ban_hanh": {**date_range, "format": date_format}}})
    if filters.so_ky_hieu:
        conditions.append({"term": {"so_ky_hieu": filters.so_ky_hieu.strip()}})
    return conditions


@app.get("/")
def serve_ui():
    return FileResponse("ui/index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


# Embedding / reranker dùng chung một GPU nhỏ và tokenizer không an toàn khi gọi song song -> chạy retrieval tuần tự;
# chỉ phần gọi LLM (chậm nhất) chạy song song giữa các request.
retrieval_lock = threading.Lock()


# Dùng `def` (không async) để FastAPI chạy trong threadpool, tránh embedding / rerank / LLM chặn event loop.
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

    start_time = time.perf_counter()
    try:
        with retrieval_lock:
            result = retrieve(
                query,
                top_search=request.top_search,
                top_rerank=min(request.top_rerank, request.top_search),
                filter_conditions=build_filters(request.filters),
            )
    except Exception as error:
        print(f"[ES error] {error}")
        raise HTTPException(status_code=502, detail="Lỗi truy vấn cơ sở dữ liệu. Kiểm tra lại bộ lọc hoặc thử lại sau.")

    search_ms, rerank_ms = result["timings"]["search_ms"], result["timings"]["rerank_ms"]
    top_chunks = result["final"]
    if not top_chunks:
        return ChatResponse(
            answer="Không tìm thấy văn bản phù hợp với bộ lọc hiện tại. Hãy thử nới lỏng bộ lọc (hiệu lực, năm ban hành, số hiệu).",
            sources=[],
            timings=Timings(search_ms=search_ms, rerank_ms=rerank_ms, llm_ms=0,
                            total_ms=elapsed_milliseconds(start_time, time.perf_counter())),
        )

    llm_start_time = time.perf_counter()
    answer = ask_legal_assistant(query=query, top_chunks=top_chunks, legal_terms=result["debug"]["legal_terms"])
    end_time = time.perf_counter()

    sources = []
    for hit in top_chunks:
        source = hit.get("_source", {})
        issue_date = None
        if source.get("ngay_ban_hanh"):
            issue_date = str(source["ngay_ban_hanh"])
        sources.append(SourceDocument(
            doc_id=str(source.get("doc_id", "")) or None,
            title=source.get("title", "Không rõ"),
            so_ky_hieu=source.get("so_ky_hieu", "Không rõ"),
            partId=str(source.get("partId", "")),
            tinh_trang_hieu_luc=source.get("tinh_trang_hieu_luc", "Không xác định"),
            ngay_ban_hanh=issue_date,
            rerank_score=hit.get("rerank_score", 0.0),
            text=source.get("text", ""),
        ))
    return ChatResponse(
        answer=answer, sources=sources,
        timings=Timings(search_ms=search_ms, rerank_ms=rerank_ms,
                        llm_ms=elapsed_milliseconds(llm_start_time, end_time),
                        total_ms=elapsed_milliseconds(start_time, end_time)),
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
