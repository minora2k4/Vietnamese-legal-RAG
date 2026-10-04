import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Elasticsearch
ES_HOST = os.getenv("ES_HOST")
INDEX_NAME = "vietnamese_legal_documents"

# Models
EMBEDDING_MODEL_NAME = "AITeamVN/Vietnamese_Embedding_v2"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
LLM_MODEL_NAME = "Qwen/Qwen3.5-9B"

# LLM Endpoint
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")