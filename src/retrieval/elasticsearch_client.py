"""Kết nối Elasticsearch (index vietnamese_legal_documents: mỗi document là một Điều luật)."""
from elasticsearch import Elasticsearch

from src.config import elasticsearch_host

elasticsearch_client = Elasticsearch(elasticsearch_host, request_timeout=30, retry_on_timeout=True, max_retries=2)
