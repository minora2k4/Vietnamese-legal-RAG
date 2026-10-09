"""Sinh câu trả lời: prompt -> LLM -> kiểm tra căn cứ (viết lại một lần nếu cần) -> hậu xử lý."""
from src.generation.answer_check import correction_message, find_unsupported, strip_unrequested_section4, warning_note
from src.generation.llm_client import chat
from src.generation.prompt import build_user_message, system_prompt


def ask_legal_assistant(query: str, top_chunks: list, legal_terms: list = None, temperature: float = 0.1) -> str:
    """Trả lời câu hỏi dựa trên các trích lục top_chunks. Lỗi kết nối LLM được trả về dưới dạng chuỗi thông báo."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": build_user_message(top_chunks, query, legal_terms)},
    ]
    try:
        answer = chat(messages, temperature)
        # Số tiền / số Điều không có trong trích lục -> yêu cầu viết lại một lần, còn sai thì gắn cảnh báo
        issues = find_unsupported(answer, top_chunks)
        if issues:
            messages += [{"role": "assistant", "content": answer},
                         {"role": "user", "content": correction_message(issues)}]
            answer = chat(messages, temperature)
            issues = find_unsupported(answer, top_chunks)
            if issues:
                answer += warning_note(issues)
        return strip_unrequested_section4(answer, query)
    except Exception as error:
        return f"Lỗi khi kết nối tới LLM: {str(error)}"
