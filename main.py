from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import time
import uvicorn

from src.es_client import hybrid_search
from src.reranker import rerank_results
from src.llm_service import ask_legal_assistant

app = FastAPI(title="Vietnamese Legal RAG API", version="1.1.0")
app.mount("/ui", StaticFiles(directory="ui"), name="ui")    
app.mount("/ui/", StaticFiles(directory="ui"), name="ui")

# Ánh xạ lựa chọn trên UI -> giá trị thực tế của trường tinh_trang_hieu_luc trong ES.
# SỬA lại cho khớp dữ liệu của bạn (None = không lọc).
STATUS_MAP = {
    "con_hieu_luc": ["Còn hiệu lực"],
    "het_mot_phan": ["Hết hiệu lực một phần"],
    "all": None,
}
DATE_FORMAT = "yyyy-MM-dd"  # định dạng của trường ngay_ban_hanh trong ES

class Filters(BaseModel):
    status: str = "con_hieu_luc"
    year_from: Optional[int] = Field(None, ge=1945, le=2100)
    year_to: Optional[int] = Field(None, ge=1945, le=2100)
    so_ky_hieu: Optional[str] = Field(None, max_length=100)

class ChatRequest(BaseModel):
    query: str = Field(..., max_length=1000)
    top_search: int = Field(10, ge=3, le=50)
    top_rerank: int = Field(3, ge=1, le=10)
    filters: Filters = Filters()

class SourceDoc(BaseModel):
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
    sources: List[SourceDoc]
    timings: Timings

def ms(a: float, b: float) -> int:
    return int((b - a) * 1000)

def build_filters(f: Filters) -> list:
    conds = []
    values = STATUS_MAP.get(f.status, STATUS_MAP["con_hieu_luc"])
    if values:
        conds.append({"terms": {"tinh_trang_hieu_luc": values}})
    rng = {}
    if f.year_from:
        rng["gte"] = f"{f.year_from}-01-01"
    if f.year_to:
        rng["lte"] = f"{f.year_to}-12-31"
    if rng:
        conds.append({"range": {"ngay_ban_hanh": {**rng, "format": DATE_FORMAT}}})
    if f.so_ky_hieu:
        conds.append({"term": {"so_ky_hieu": f.so_ky_hieu.strip()}})
    return conds

@app.get("/")
def serve_ui():
    return FileResponse("ui/index.html")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

# Dùng `def` (không async) để FastAPI chạy trong threadpool,
# tránh việc embedding/rerank/LLM chặn event loop khi có nhiều người dùng.
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

    t0 = time.perf_counter()
    try:
        es_response = hybrid_search(
            query_text=query,
            top_k=request.top_search,
            filter_conditions=build_filters(request.filters),
        )
    except Exception as e:
        print(f"[ES error] {e}")
        raise HTTPException(status_code=502, detail="Lỗi truy vấn cơ sở dữ liệu. Kiểm tra lại bộ lọc hoặc thử lại sau.")

    t1 = time.perf_counter()  # embedding + Elasticsearch
    raw_hits = es_response["hits"]["hits"]
    if not raw_hits:
        return ChatResponse(
            answer="Không tìm thấy văn bản phù hợp với bộ lọc hiện tại. Hãy thử nới lỏng bộ lọc (hiệu lực, năm ban hành, số hiệu).",
            sources=[],
            timings=Timings(search_ms=ms(t0, t1), rerank_ms=0, llm_ms=0, total_ms=ms(t0, t1)),
        )

    top_chunks = rerank_results(query_text=query, search_hits=raw_hits,
                                top_k=min(request.top_rerank, request.top_search))
    t2 = time.perf_counter()
    answer = ask_legal_assistant(query=query, top_chunks=top_chunks)
    t3 = time.perf_counter()

    sources = []
    for hit in top_chunks:
        src = hit.get("_source", {})
        sources.append(SourceDoc(
            title=src.get("title", "Không rõ"),
            so_ky_hieu=src.get("so_ky_hieu", "Không rõ"),
            partId=str(src.get("partId", "")),
            tinh_trang_hieu_luc=src.get("tinh_trang_hieu_luc", "Không xác định"),
            ngay_ban_hanh=str(src["ngay_ban_hanh"]) if src.get("ngay_ban_hanh") else None,
            rerank_score=hit.get("rerank_score", 0.0),
            text=src.get("text", ""),
        ))
    return ChatResponse(
        answer=answer, sources=sources,
        timings=Timings(search_ms=ms(t0, t1), rerank_ms=ms(t1, t2), llm_ms=ms(t2, t3), total_ms=ms(t0, t3)),
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)