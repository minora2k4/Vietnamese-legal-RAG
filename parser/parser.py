import re
import os
from typing import List, Tuple
from parser.part import LEGAL_DOC_ARCS, Part

def line2part(line, doc_arc=LEGAL_DOC_ARCS["type_1"], current_level=None):
    """
    Nhận diện loại cấu trúc và số thứ tự (ID) của một dòng văn bản pháp luật.
    
    Returns:
        tuple: (part_type, part_id) hoặc (None, None) nếu không khớp.
        Ví dụ: ("Điều", "1"), ("Phần", "I"), ("Điểm", "a")
    """
    # Chuẩn hóa chuỗi đầu vào (về chữ thường để xử lý và loại bỏ khoảng trắng thừa)
    line_clean = line.strip()
    if len(line_clean) <= 3:
        # Kiểm tra xem dòng này có phải chỉ chứa mỗi ID và dấu định dạng không
        if re.match(r"^(\d+[\.\s]*|[abcdđeghiklmnopqrstuvxyz]\)?)$", line_clean, re.IGNORECASE):
            return None, None
    line_lower = line_clean.lower()
    # Định nghĩa danh sách các cấp độ từ cao đến thấp dựa trên doc_arc
    levels_order = [lvl.strip().lower() for lvl in doc_arc.split(',')]
    # Giới hạn các cấp độ được phép dựa trên current_level
    if current_level:
        current_level_lower = current_level.strip().lower()
        if current_level_lower in levels_order:
            cutoff_idx = levels_order.index(current_level_lower)
            allowed_levels = levels_order[cutoff_idx:]
        else:
            allowed_levels = levels_order
    else:
        allowed_levels = levels_order
    # 2. Định nghĩa các mẫu Regex (tất cả viết thường) và bắt nhóm (group) để lấy ID
    # Sử dụng ([ivxlcmd]+) cho số La Mã và (\d+) cho số thường
    patterns = {
        "phần": r"^phần\s+(?:thứ\s+)?([ivxlcmd]+\b|\d+\b|[a-zđđếúậáàảãạéèẻẽẹíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ\s]+$)",
        "chương": r"^chương\s+([ivxlcmd]+|\d+)", 
        "mục": r"^mục\s+(\d+)", 
        "tiểu mục": r"^tiểu\s*mục\s+(\d+)", 
        # "điều": r"^điều\s+(\d+)(?:\s*[\.\:\)\-\,]|\s*$)", 
        "điều": r"^điều\s+(\d+[a-zđ]?)", 
        "khoản": r"^(\d+[a-zđ]?)(?:[\.\s\n\)\-])", # Khoản 1. hoặc 1 hoặc 1a.
        "điểm": r"^([abcdđeghiklmnopqrstuvxyz])[\)\/]" # Điểm a)
    }
    # 3. Duyệt qua các cấp độ được phép
    for level in allowed_levels:
        if level in patterns:
            match = re.match(patterns[level], line_lower, re.IGNORECASE)
            if match:
                # Lấy giá trị ID/Số thứ tự nằm trong cặp dấu ngoặc đơn () của regex
                part_id = match.group(1)
                # Nếu là Khoản hoặc Điểm, giữ nguyên chữ thường/số. 
                # Nếu là từ khóa khác, có thể giữ nguyên text gốc trong văn bản để làm ID (ví dụ: "I" hoặc "thứ nhất")
                # Chuẩn hóa tên Loại để trả về (chữ cái đầu viết hoa)
                part_type = level.capitalize() if level != "tiểu mục" else "Tiểu mục"
                # Trả về kết quả dưới dạng tuple nguyên bản từ văn bản gốc (giữ nguyên hoa thường của ID gốc)
                # Tìm vị trí text khớp của ID trong chuỗi gốc ban đầu để lấy chính xác ký tự Hoa/Thường (ví dụ: "Phần I" -> "I")
                start, end = match.span(1)
                original_id = line_clean[start:end]
                return part_type, original_id
    return None, None


def count_quote(line, quote_balance=0):
    """ Count number of quote marks `"` in a line """
    quote_balance += line.count("\"")
    return quote_balance

def quote_parser(line_idx, lines):
    """ Simple parser for lines contain quotes """
    quote_text = ""
    quote_balance = 0
    while line_idx < len(lines):
        line = lines[line_idx]
        quote_balance = count_quote(line, quote_balance)
        if quote_balance % 2 == 1:
            quote_text += line + "\n"
            line_idx += 1
        else:
            quote_text += line
            break   
    return quote_text, line_idx

def parser(legal_markdown, doc_arc=LEGAL_DOC_ARCS["type_1"], force_paragraph_ending=True):
    """ 
    Ultimate Regex Parser for Vietnamese legal documents. 
    This function would parse a raw legal document in markdown into legal tree
    A legal tree structure contains 3 main sections:
        - "intro": Contain relevant info and metadata of the document
        - "content": Main legal tree need to be parsed (based on LEGAL_DOC_ARCS)
        - "end": Contain final paragraph (often be the signer or additional informtion) or Appendices
    The "content" section get parsed into a tree-like with each node in form of a Part:
        ```
        class Part:
            partType: str
            partId: str
            treeId: str
            text: str
            children: list[Part] = field(default_factory=list)
        ```
    """
    # Initialize legal document tree
    legal_tree = {
        "intro": {
            "text": ""
        },
        "content": {
            "parts": []
        },
        "end": {
            "text": ""
        }
    }
    levels_order = [lvl.strip().lower() for lvl in doc_arc.split(',')]
    # Start parser here
    line_idx = 0
    # Start parsing intro here
    lines = legal_markdown.splitlines()
    while line_idx < len(lines):
        part_type, _ = line2part(lines[line_idx], doc_arc)
        if not part_type:
            legal_tree["intro"]["text"] += lines[line_idx] + "\n"
            line_idx += 1
        else:  
            # Finish parsing intro, now parsing content section
            break
    # Start parsing content here
    is_last_content_line = False
    level_stack: List[Tuple[str, Part]] = []
    while line_idx < len(lines) and not is_last_content_line:
        line = lines[line_idx]
        # Check if line contain quote
        if count_quote(line) % 2 == 1:
            quote_text, line_idx = quote_parser(line_idx, lines)
            # This line is continuation text for the currently active part
            if level_stack:
                level_stack[-1][1].text += "\n" + quote_text
            line_idx += 1
            continue
        if "./." in line:
            is_last_content_line = True
        part_type, part_id = line2part(line, doc_arc)
        if not part_type: 
            # This line is continuation text for the currently active part
            if level_stack:
                level_stack[-1][1].text += "\n" + line
            line_idx += 1
            continue
        # Clean up the type to match our order list
        part_type = part_type.strip().lower()
        part_level = levels_order.index(part_type)
        # Pop elements off the stack until we find a valid parent level
        while level_stack:
            parent_type, _ = level_stack[-1]
            parent_level = levels_order.index(parent_type)
            if parent_level < part_level:
                # Found the parent! Stop popping.
                break
            else:
                # Not the parent (same level or higher up), remove it
                level_stack.pop()
        # Build the hierarchical treeId based on current stack state
        parent_path = "_".join([f"{p_type}{p_obj.partId}" for p_type, p_obj in level_stack])
        tree_id = f"{parent_path}_{part_type}{part_id}" if parent_path else f"{part_type}{part_id}"
        # Create the new part
        new_part = Part(partType=part_type, partId=part_id, treeId=tree_id, text=line)
        # Append to parent's children, or to root level if stack is empty
        if level_stack:
            level_stack[-1][1].children.append(new_part)
        # Edge case: "khoản" or "điểm" can not be the beginning part
        elif len(legal_tree["content"]["parts"]) == 0 and (part_type == "khoản" or part_type == "điểm"):
            legal_tree["intro"]["text"] += lines[line_idx] + "\n"
        else:
            legal_tree["content"]["parts"].append(new_part)
        # Push this new part onto the stack as the current active block
        level_stack.append((part_type, new_part))
        line_idx += 1 # Advance to next line
    # Add remaining to end section
    while line_idx < len(lines):
        legal_tree["end"]["text"] += lines[line_idx] + "\n"
        line_idx += 1 # Advance to next line
    # Now process edge case for end section
    ## If `end` section has not been parsed
    if len(legal_tree["end"]["text"]) == 0 and len(legal_tree["content"]["parts"]) > 0:
        ## Now retrieve and analyze the last part 
        last_part = legal_tree["content"]["parts"][-1]
        while len(last_part.children) > 0:
            last_part = last_part.children[-1]
        paragraphs = re.split(r'\n\s*\n', last_part.text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        ## Now check 2nd paragraph to check if it is a possible ending
        if len(paragraphs) > 1:    
            end_text = "\n".join(paragraphs[1:])
            if re.search(r'^\||(?:nơi nhận|chủ tịch quốc hội|phụ lục)', end_text.lower(), re.IGNORECASE):
                # Edit the last part and get new ending
                last_part.text = paragraphs[0]
                legal_tree["end"]["text"] = end_text
            elif force_paragraph_ending:
                # Force 2nd - n(th) paragraph
                last_part.text = paragraphs[0]
                legal_tree["end"]["text"] = end_text
    return legal_tree

def parse_part(legal_markdown, doc_arc=LEGAL_DOC_ARCS["type_1"]):
    """
    Parse a legal part (Điều/Khoản/Điểm/...) into a Part tree.

    Returns:
        List[Part]
    """
    levels_order = [lvl.strip().lower() for lvl in doc_arc.split(",")]
    level_stack: List[Tuple[str, Part]] = []
    root_parts = []
    lines = legal_markdown.splitlines()
    line_idx = 0
    while line_idx < len(lines):
        line = lines[line_idx]
        # quoted block
        if count_quote(line) % 2 == 1:
            quote_text, line_idx = quote_parser(line_idx, lines)
            if level_stack:
                level_stack[-1][1].text += "\n" + quote_text
            line_idx += 1
            continue
        part_type, part_id = line2part(line, doc_arc)
        # continuation text
        if not part_type:
            if level_stack:
                level_stack[-1][1].text += "\n" + line
            line_idx += 1
            continue
        part_type = part_type.lower().strip()
        part_level = levels_order.index(part_type)
        while level_stack:
            parent_type, _ = level_stack[-1]
            parent_level = levels_order.index(parent_type)
            if parent_level < part_level:
                break
            level_stack.pop()
        parent_path = "_".join(
            f"{t}{p.partId}"
            for t, p in level_stack
        )
        tree_id = (
            f"{parent_path}_{part_type}{part_id}"
            if parent_path
            else f"{part_type}{part_id}"
        )
        new_part = Part(
            partType=part_type,
            partId=part_id,
            treeId=tree_id,
            text=line,
        )
        if level_stack:
            level_stack[-1][1].children.append(new_part)
        else:
            root_parts.append(new_part)
        level_stack.append((part_type, new_part))
        line_idx += 1
    return root_parts

def preprocess_modify_content(content):
    terms = content.split(":", 1)
    if len(terms) > 1:
        content = terms[1]
    # Remove leading characters until the first letter or digit
    content = re.sub(r'^[^A-Za-zÀ-ỹ0-9]+', '', content)
    # Remove trailing quotes
    content = re.sub(r"""['"]+\s*$""", "", content)
    return content

def parse_modify_content(content):
    content = preprocess_modify_content(content)
    part = parse_part(content)
    return part