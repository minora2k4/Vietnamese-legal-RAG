"""Mẫu kiểm tra câu trả lời của LLM: số tiền / số Điều phải có trong trích lục; mục 4 chỉ giữ khi hỏi về xử phạt."""
import re

# Thông tin phải truy được về trích lục: số tiền và số Điều
money_pattern = re.compile(r"\d{1,3}(?:\.\d{3})+(?=\s*(?:đồng|VNĐ|vnđ))")
article_number_pattern = re.compile(r"Điều\s+(\d{1,4})")

# Mục 4 (hình phạt bổ sung / biện pháp khắc phục) của định dạng trả lời, chỉ giữ khi câu hỏi liên quan xử phạt
section4_pattern = re.compile(r"\n\s*\*\*4\.[^\n]*\*\*.*", re.S)
penalty_intent_pattern = re.compile(r"phạt|vi phạm|tội|truy cứu|xử lý|kỷ luật|bồi thường|chế tài|tước|tạm giữ", re.I)
