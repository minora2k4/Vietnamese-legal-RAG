"""Cấu hình chung: biến môi trường (.env)"""
import os

from dotenv import load_dotenv

load_dotenv()  

# Elasticsearch
elasticsearch_host = os.getenv("ES_HOST")
index_name = "vietnamese_legal_documents"

# Model
embedding_model_name = "AITeamVN/Vietnamese_Embedding_v2"
reranker_model_name = "BAAI/bge-reranker-v2-m3"
llm_model_name = "Qwen/Qwen3.5-9B"

# Endpoint LLM (vLLM tự host trên Kaggle sau Cloudflare tunnel, URL đổi mỗi phiên)
llm_base_url = os.getenv("LLM_BASE_URL")
llm_api_key = os.getenv("LLM_API_KEY")
