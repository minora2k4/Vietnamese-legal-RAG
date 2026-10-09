"""Gọi LLM (Qwen3.5-9B trên vLLM, API tương thích OpenAI)."""
from openai import OpenAI

from src.config import llm_api_key, llm_base_url, llm_model_name

client = OpenAI(base_url=llm_base_url, api_key=llm_api_key)


def chat(messages: list, temperature: float) -> str:
    """Một lượt hội thoại; tắt chế độ suy nghĩ (thinking) của Qwen để trả lời nhanh hơn."""
    response = client.chat.completions.create(
        model=llm_model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=2048,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return response.choices[0].message.content
