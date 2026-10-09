"""Kiểm tra câu trả lời của LLM sau khi sinh (Qwen 9B đôi khi lấy mức phạt từ kiến thức sẵn có, trích Điều không có).

- Số tiền / số Điều trong câu trả lời phải xuất hiện trong các trích lục đã đưa cho LLM.
- Mục 4 (hình phạt bổ sung) bị bỏ nếu câu hỏi không liên quan xử phạt.
Mẫu nhận diện nằm trong rule base src/rules/answers.py."""
from typing import Dict, List

from src.rules.answers import article_number_pattern, money_pattern, penalty_intent_pattern, section4_pattern


def find_unsupported(answer: str, chunks: List[dict]) -> Dict[str, List[str]]:
    """Số tiền / số Điều xuất hiện trong câu trả lời nhưng không có trong trích lục (kể cả nội dung dẫn chiếu).
    Trả về {"money": [...], "dieu": [...]} (chỉ gồm các loại có vi phạm)."""
    chunk_texts = []
    for chunk in chunks:
        chunk_texts.append(chunk.get("_source", {}).get("text") or "")
    context_text = " ".join(chunk_texts)

    # Số tiền và số Điều có trong trích lục (số Điều gồm cả Điều của chính trích lục và các Điều được dẫn chiếu)
    context_money = set(money_pattern.findall(context_text))
    context_articles = set()
    for chunk in chunks:
        context_articles.add(str(chunk.get("_source", {}).get("partId")))
    context_articles.update(article_number_pattern.findall(context_text))

    unsupported_money = set()
    for amount in money_pattern.findall(answer):
        if amount not in context_money:
            unsupported_money.add(amount)

    unsupported_articles = set()
    for number in article_number_pattern.findall(answer):
        if number not in context_articles:
            unsupported_articles.add(number)

    issues = {}
    if unsupported_money:
        issues["money"] = sorted(unsupported_money)
    if unsupported_articles:
        issues["dieu"] = sorted(unsupported_articles, key=int)
    return issues


def correction_message(issues: Dict[str, List[str]]) -> str:
    """Yêu cầu LLM viết lại, liệt kê cụ thể các nội dung không có căn cứ."""
    parts = []
    if issues.get("money"):
        amounts = []
        for amount in issues["money"]:
            amounts.append(f"{amount} đồng")
        parts.append("các số tiền " + ", ".join(amounts))
    if issues.get("dieu"):
        articles = []
        for number in issues["dieu"]:
            articles.append(f"Điều {number}")
        parts.append("các điều " + ", ".join(articles))
    return (f"Câu trả lời trên có nội dung KHÔNG có trong các trích lục: {'; '.join(parts)}. "
            "Hãy viết lại câu trả lời theo đúng định dạng, chỉ dùng thông tin có trong các trích lục; "
            "không dùng kiến thức bên ngoài. Nếu các trích lục không có thông tin để trả lời một ý, ghi rõ "
            "\"Chưa tìm thấy quy định trong dữ liệu cho nội dung này\".")


def warning_note(issues: Dict[str, List[str]]) -> str:
    """Cảnh báo gắn vào câu trả lời khi viết lại vẫn còn nội dung không có căn cứ."""
    items = []
    for amount in issues.get("money", []):
        items.append(f"{amount} đồng")
    for number in issues.get("dieu", []):
        items.append(f"Điều {number}")
    return ("\n\n> **Lưu ý:** chưa đối chiếu được với các văn bản được truy xuất các nội dung sau: "
            + ", ".join(items) + ". Vui lòng kiểm tra lại văn bản gốc trước khi sử dụng.")


def strip_unrequested_section4(answer: str, query: str) -> str:
    """Rule-based: bỏ mục 4 (hình phạt bổ sung) khi câu hỏi không liên quan xử phạt."""
    if penalty_intent_pattern.search(query):
        return answer
    return section4_pattern.sub("", answer).rstrip()
