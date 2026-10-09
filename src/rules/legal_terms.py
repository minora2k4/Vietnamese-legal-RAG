"""Luật bổ sung thuật ngữ pháp lý cho cách nói đời thường: reranker không tự nối được "đuổi việc" với
"đơn phương chấm dứt hợp đồng lao động", nên câu hỏi được bổ sung thuật ngữ trước khi tìm kiếm / rerank."""
import re
from typing import List, Tuple

regex_flags = re.IGNORECASE | re.UNICODE

# (mẫu cách nói đời thường, thuật ngữ pháp lý bổ sung)
lay_phrases = [
    # Lao động
    (r"đuổi việc|cho (?:tôi |em |anh |chị |người lao động |nhân viên )?nghỉ việc|bị cho nghỉ|cắt hợp đồng|cho thôi việc",
     "người sử dụng lao động đơn phương chấm dứt hợp đồng lao động"),
    (r"\bsa thải\b", "kỷ luật sa thải; người sử dụng lao động đơn phương chấm dứt hợp đồng lao động"),
    (r"nghỉ ngang|tự ý nghỉ việc|tự nghỉ việc|xin nghỉ việc|muốn nghỉ việc|bỏ việc",
     "người lao động đơn phương chấm dứt hợp đồng lao động"),
    (r"nợ lương|chậm lương|chậm trả lương|không trả lương|trả lương chậm|không được trả lương|quỵt lương",
     "không được trả đủ lương hoặc trả lương không đúng thời hạn"),
    (r"tăng ca|\bOT\b", "làm thêm giờ"),
    (r"nghỉ đẻ|nghỉ sinh(?: con)?", "nghỉ thai sản"),
    (r"ốm đau|bị ốm|bị bệnh|điều trị dài ngày|nằm viện", "người lao động bị ốm đau, tai nạn đã điều trị"),
    (r"lương tối thiểu|lương cơ bản", "mức lương tối thiểu"),
    # Hôn nhân gia đình
    (r"ly dị|bỏ chồng|bỏ vợ", "ly hôn"),
    (r"tiền nuôi con|chu cấp cho con|trợ cấp nuôi con", "nghĩa vụ cấp dưỡng"),
    (r"(?:giành|tranh) quyền nuôi con|quyền nuôi con|ai (?:được )?nuôi con",
     "người trực tiếp nuôi con sau khi ly hôn"),
    (r"đánh đập|bạo hành|đánh vợ|đánh chồng|đánh con", "hành vi bạo lực gia đình"),
    (r"lấy chồng|lấy vợ|cưới (?:vợ|chồng|nhau)", "kết hôn; vợ chồng"),
    # Thừa kế
    (r"(?:mất|chết|qua đời|từ trần)\b[^.?!]*\b(?:không|chưa)\s+(?:để lại|lập|viết|có)\s+di chúc|"
     r"(?:không|chưa)\s+(?:để lại|lập|viết|có)\s+di chúc[^.?!]*\b(?:mất|chết|qua đời|từ trần)",
     "thừa kế theo pháp luật; người thừa kế theo pháp luật, hàng thừa kế"),
    (r"(?:mất|chết|qua đời|từ trần)\b[^.?!]*\bchia\b|\bchia\b[^.?!]*(?:tài sản|nhà|đất|tiền)[^.?!]*(?:mất|chết|qua đời)",
     "chia di sản thừa kế"),
    # Cư trú, hộ tịch, giấy tờ
    (r"hộ khẩu|nhập khẩu|chuyển khẩu|cắt khẩu", "đăng ký thường trú"),
    (r"\bKT3\b|đăng ký ở tạm", "đăng ký tạm trú"),
    (r"(?:làm|xin) (?:giấy )?khai sinh", "đăng ký khai sinh"),
    (r"làm (?:căn cước|CCCD|chứng minh(?: nhân dân| thư)?)", "cấp thẻ căn cước"),
    # Đất đai, nhà ở, dân sự
    (r"sổ đỏ|sổ hồng", "giấy chứng nhận quyền sử dụng đất, quyền sở hữu nhà ở"),
    (r"sang tên (?:đất|nhà|sổ)|mua bán đất|bán đất", "chuyển nhượng quyền sử dụng đất"),
    (r"nứt tường|nứt nhà|sụt lún|sập (?:nhà|tường)|đổ (?:nhà|tường)|xây nhà (?:làm|gây)",
     "bồi thường thiệt hại do nhà cửa, công trình xây dựng gây ra"),
    (r"đòi bồi thường|đền bù|đền tiền|bắt đền", "trách nhiệm bồi thường thiệt hại"),
    (r"vay (?:tiền )?không trả|quỵt nợ|xù nợ|giật nợ", "nghĩa vụ trả nợ; tội lạm dụng tín nhiệm chiếm đoạt tài sản"),
    (r"mua phải hàng (?:giả|kém chất lượng|lỗi|hỏng)|hàng (?:giả|lỗi) không cho đổi", "quyền của người tiêu dùng"),
    # Hình sự
    (r"(?:\d{1,2}|mười \w+) tuổi\b[^.?!]*(?:truy cứu|đi tù|ngồi tù|xử lý hình sự|trách nhiệm hình sự|phạm tội)|"
     r"(?:truy cứu|đi tù|ngồi tù|trách nhiệm hình sự)[^.?!]*\b\d{1,2} tuổi",
     "tuổi chịu trách nhiệm hình sự; người dưới 18 tuổi phạm tội"),
    (r"đánh (?:người|bạn|nhau|hàng xóm)|gây thương tích|đâm (?:người|bạn)|chém (?:người|nhau)",
     "tội cố ý gây thương tích hoặc gây tổn hại cho sức khỏe của người khác"),
    (r"đi tù|ngồi tù|bị tù", "hình phạt tù"),
    (r"ăn trộm|ăn cắp|trộm đồ|trộm xe", "tội trộm cắp tài sản"),
    (r"lừa tiền|bị lừa|lừa đảo qua mạng", "tội lừa đảo chiếm đoạt tài sản"),
    (r"cá độ|đánh bài ăn tiền|chơi bạc", "tội đánh bạc"),
    # Giao thông
    (r"xe máy", "xe mô tô, xe gắn máy"),
    (r"vượt đèn đỏ|vượt đèn vàng|chạy đèn đỏ", "không chấp hành hiệu lệnh của đèn tín hiệu giao thông"),
    (r"(?:uống|say) (?:rượu|bia)|nhậu|nồng độ cồn|thổi (?:nồng độ|cồn)",
     "điều khiển xe mà trong máu hoặc hơi thở có nồng độ cồn"),
    (r"bằng lái", "giấy phép lái xe"),
    (r"chạy quá tốc độ|vượt tốc độ|phóng nhanh", "điều khiển xe chạy quá tốc độ quy định"),
    (r"không đội mũ bảo hiểm", "không đội mũ bảo hiểm cho người đi mô tô, xe máy"),
]

# Biên dịch sẵn các mẫu: [(regex, thuật ngữ pháp lý)]
lay_to_legal_terms: List[Tuple[re.Pattern, str]] = []
for lay_pattern, legal_term in lay_phrases:
    lay_to_legal_terms.append((re.compile(lay_pattern, regex_flags), legal_term))
