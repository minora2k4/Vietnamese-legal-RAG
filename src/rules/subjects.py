"""Nhóm đối tượng áp dụng loại trừ nhau: câu hỏi về một đối tượng (xe máy) không được trả lời bằng Điều có tiêu đề
nêu đối tượng khác cùng nhóm (xe máy chuyên dùng, xe đạp)."""
import re

# nhóm -> {tên đối tượng: mẫu nhận diện trong câu hỏi / tiêu đề Điều}
subject_groups = {
    "phương tiện giao thông": {
        "ô tô": re.compile(r"\bô tô\b|\bxe hơi\b", re.I),
        "mô tô": re.compile(r"mô tô|gắn máy|xe máy(?! chuyên dùng)", re.I),   # "xe máy" thường ngày = mô tô, gắn máy
        "xe máy chuyên dùng": re.compile(r"xe máy chuyên dùng", re.I),
        "xe đạp, xe thô sơ": re.compile(r"xe đạp|xe thô sơ|xích lô", re.I),
        "người đi bộ": re.compile(r"người đi bộ", re.I),
    },
}
