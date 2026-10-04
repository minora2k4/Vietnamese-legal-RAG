from openai import OpenAI
from src.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME
from src.prompt import SYSTEM_PROMPT, build_user_message

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

def ask_legal_assistant(query: str, top_chunks: list, temperature: float = 0.1) -> str:
    user_message = build_user_message(top_chunks, query)
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=2048,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            }
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Lỗi khi kết nối tới LLM: {str(e)}"