"""Lọc theo đối tượng áp dụng: câu hỏi về "xe máy" không dùng Điều có tiêu đề "... xe máy chuyên dùng"
(nhóm đối tượng loại trừ nhau khai báo trong rule base src/rules/subjects.py)."""
from typing import Dict

from src.rules.subjects import subject_groups


def find_subjects(text: str) -> Dict[str, set]:
    """Đối tượng (theo từng nhóm trong rule base) được nhắc trong text: {nhóm: {tên đối tượng}}."""
    found = {}
    for group, members in subject_groups.items():
        names = set()
        for name, pattern in members.items():
            if pattern.search(text):
                names.add(name)
        if names:
            found[group] = names
    return found


def subject_mismatch(query_subjects: Dict[str, set], source: dict) -> bool:
    """Rule-based: tiêu đề Điều nêu đối tượng của một nhóm mà không trùng đối tượng nào câu hỏi nêu trong nhóm đó."""
    if not query_subjects:
        return False
    heading = (source.get("text") or "").split("\n", 1)[0]
    heading_subjects = find_subjects(heading)
    for group, names in query_subjects.items():
        if group not in heading_subjects:
            continue
        shared_subjects = heading_subjects[group] & names
        if not shared_subjects:
            return True
    return False
