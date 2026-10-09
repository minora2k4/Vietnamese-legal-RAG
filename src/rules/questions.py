"""Luật về cách đặt câu hỏi tiếng Việt: câu so sánh, câu nhiều vế, đại từ thay thế, câu hỏi tổng quan về một văn bản."""
import re

# Câu so sánh -> 2 vế (thứ tự quan trọng: "A và B khác nhau" phải xét trước "A khác B")
comparison_patterns = [
    re.compile(r"^(?:hãy\s+)?(?:so sánh|phân biệt)\s+(?:giữa\s+)?(.+?)\s+(?:và|với)\s+(.+?)[\s?.]*$", re.I),
    re.compile(r"^(?:sự\s+)?khác nhau giữa\s+(.+?)\s+(?:và|với)\s+(.+?)(?:\s+là gì)?[\s?.]*$", re.I),
    re.compile(r"^(.+?)\s+và\s+(.+?)\s+khác nhau(?:\s+(?:như thế nào|thế nào|ở điểm nào|ra sao|chỗ nào))?[\s?.]*$", re.I),
    re.compile(r"^(.+?)\s+(?:khác với|khác|so với)\s+(?!nhau)(.+?)(?:\s+(?:như thế nào|thế nào|ở điểm nào|ra sao|chỗ nào))?[\s?.]*$", re.I),
]

# Câu nhiều vế nối bằng "và", vế sau bắt đầu bằng một trong các từ này: "X được giao cho ai và Y có nghĩa vụ gì?"
multi_part_split_pattern = re.compile(r"\s*(?:,\s*)?\bvà\b\s+(?=(?:khi đó|người|nếu|thì|mức|hồ sơ|thủ tục|ai|có|phải|"
                                      r"được|bị|hàng|thời|khi|trường hợp|nguyên tắc|tài sản)\b)")

# Từ để hỏi (một vế phải có từ để hỏi mới được coi là một câu hỏi riêng)
question_word_pattern = re.compile(r"\b(gì|nào|ai|bao nhiêu|bao lâu|thế nào|ra sao|không|sao|đâu|khi nào)\b", re.I)

# Phần đuôi hỏi của câu ("như thế nào", "là gì"...), bỏ đi để lấy phần điều kiện của vế trước
question_tail_pattern = re.compile(r"\s*(?:như thế nào là|như thế nào|thế nào là|thế nào|ra sao|là gì|là ai|"
                                   r"là bao nhiêu|bao nhiêu|gồm những gì|gồm những ai|những gì|những ai|nào|gì)\b", re.I)

# Đại từ ở vế sau thay cho điều kiện / chủ thể của vế trước
condition_reference_pattern = re.compile(r"\b(khi đó|trường hợp đó|trường hợp này|lúc đó)\b", re.I)
subject_reference_pattern = re.compile(r"\b(họ|người đó|người này)\b", re.I)

# Chủ thể của vế trước = phần đứng trước động từ đầu tiên
subject_end_pattern = re.compile(r"\s+(?:được|phải|có|bị|là|sẽ|cần|thì)\s+")

# Câu hỏi tổng quan về một văn bản được nêu tên, không hỏi nội dung cụ thể ("Nghị định 168/2024 quy định về những gì?",
# "phạm vi điều chỉnh của Thông tư 02/2021") -> trả lời bằng Điều 1 (phạm vi điều chỉnh) của văn bản
document_overview_pattern = re.compile(r"phạm vi điều chỉnh|(?:quy định|điều chỉnh|đề cập|nói|có)\s+(?:về\s+)?"
                                       r"(?:những\s+|các\s+)?(?:nội dung|vấn đề|lĩnh vực|điều)?\s*(?:gì|nào)"
                                       r"(?:\s+khác)?\s*[?.]*\s*$", re.I)
