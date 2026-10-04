#!/bin/bash

# Dừng script ngay nếu có lệnh bị lỗi ngoại trừ lệnh curl kiểm tra
set -e

echo "=================================================="
echo "ĐANG KHỞI ĐỘNG HỆ THỐNG TRỢ LÝ PHÁP LUẬT RAG AI"
echo "=================================================="

# 1. Kích hoạt môi trường ảo Python (Uncomment nếu bạn cần kích hoạt env)
# source ~/miniconda3/bin/activate python3.10

# 2. Khởi động Docker Compose
echo "Đang khởi động dịch vụ Elasticsearch & Kibana qua Docker..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
elif docker compose version &> /dev/null; then
    docker compose up -d
else
    echo "LỖI: Không tìm thấy Docker Compose trên máy!"
    exit 1
fi

# 3. Vòng lặp chờ Elasticsearch sẵn sàng (Retry loop)
ES_HOST="http://localhost:9200"
echo "Đang chờ Elasticsearch (es_rag_law) khởi động hoàn tất tại ${ES_HOST}..."

MAX_RETRIES=30
RETRY_COUNT=0

# Tắt tạm 'set -e' để vòng lặp curl không làm dừng script khi ES chưa phản hồi
set +e
while true; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${ES_HOST}" || echo "000")
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo ""
        echo "Elasticsearch đã khởi động thành công và sẵn sàng kết nối!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo ""
        echo "LỖI: Quá thời gian chờ ($((MAX_RETRIES * 3)) giây). Elasticsearch không thể khởi chạy!"
        echo "Hãy kiểm tra log container bằng lệnh: docker logs es_rag_law"
        exit 1
    fi

    echo -n "."
    sleep 3
done
set -e

# 4. Thiết lập biến môi trường
echo "--------------------------------------------------"
echo "Cấu hình môi trường:"
echo "   - ES Host: $ES_HOST"
echo "   - LLM Endpoint: $LLM_BASE_URL"
echo "--------------------------------------------------"

# 5. Khởi chạy FastAPI Server bằng Uvicorn
echo "Đang khởi chạy FastAPI Server..."
echo "Web UI Chat: http://localhost:8000"
echo "API Docs:   http://localhost:8000/docs"
echo "=================================================="

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload