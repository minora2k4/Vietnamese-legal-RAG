"""Module SINH CÂU TRẢ LỜI: từ các Điều đã chọn -> câu trả lời của LLM.

- prompt.py       : system prompt và user message (trích lục kèm nhãn hiệu lực, câu hỏi, yêu cầu)
- llm_client.py   : gọi LLM qua API tương thích OpenAI (vLLM)
- answer_check.py : kiểm tra số tiền / số Điều trong câu trả lời có căn cứ, bỏ mục 4 khi không hỏi về xử phạt
- assistant.py    : ask_legal_assistant() = prompt -> LLM -> kiểm tra -> viết lại nếu cần
"""
