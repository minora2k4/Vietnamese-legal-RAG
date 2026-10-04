from __future__ import annotations
from dataclasses import dataclass, field

# All legal document architectures
"""
Bố cục văn bản pháp luật
1. Phần mở đầu:
 - Quốc hiệu  “CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM” viết in hoa, cỡ chữ 12 - 13, trình bày ở phía trên cùng, bên phải và được thể hiện bằng kiểu chữ đứng, đậm. 
 - Tiêu ngữ “Độc lập - Tự do - Hạnh phúc” được đặt ngay dưới Quốc hiệu, cỡ chữ 13 - 14, thể hiện bằng kiểu chữ đứng, đậm; từng từ cách nhau bằng dấu “-”. 
 - Tên cơ quan ban hành chính là tên chính thức của cơ quan có thẩm quyền ban hành văn bản đó. 
 - Số, ký hiệu của văn bản gồm số thứ tự, năm ban hành, loại văn bản và cơ quan đã ban hành. 
 - Địa danh là tên gọi chính thức của tỉnh, thành phố trực thuộc trung ương nơi cơ quan ban hành văn bản đang đóng trụ sở. 
 - Ngày - tháng - năm ban hành chính là thời điểm mà văn bản đó được thông qua hoặc ký ban hành. 
 - Tên văn bản gồm tên loại văn bản đó và tên gọi để phản ánh khái quát nội dung văn bản. 
 - Căn cứ ban hành văn bản - chính là văn bản quy phạm pháp luật dùng để làm cơ sở ban hành. 
2. Phần nội dung: Định nghĩa như sau:
    - "type_1": "Phần, chương, Mục, tiểu Mục, Điều, Khoản, điểm",
    - "type_2": "Phần, chương, Mục, Điều, Khoản, điểm",
    - "type_3": "Chương, Mục, tiểu Mục, Điều, Khoản, điểm",
    - "type_4": "Chương, Mục, Điều, Khoản, điểm",
    - "type_5": "Chương, Điều, Khoản, điểm",
    - "type_6": "Điều, Khoản, điểm",
3. Phần kết thúc:
Phần kết thúc của một văn bản pháp luật cũng sẽ khác với các văn bản thông thường. Nội dung phần này sẽ chứa đựng nhiều thông tin quan trọng cần chú ý. Theo Điều 64, nghị định 34/2016/NĐ-CP có quy định rõ về việc trình bày như sau: 
 - Chức vụ, họ tên và chữ ký của người có thẩm quyền ban hành văn bản pháp luật đó. Trong trường hợp ký thay cũng phải thể hiện rõ ràng ràng và có ghi tắt “KT” ở bên cạnh. 
 - Dấu của cơ quan ban hành văn bản đóng ngay sau khi có chữ ký của người có thẩm quyền. 
 - Nơi nhận gồm các cơ quan giám sát, kiểm tra, ban hành và các cơ quan khác tùy văn bản. 
"""
LEGAL_DOC_ARCS = {
    "type_1": "Phần, chương, Mục, tiểu Mục, Điều, Khoản, điểm",
    "type_2": "Phần, chương, Mục, Điều, Khoản, điểm",
    "type_3": "Chương, Mục, tiểu Mục, Điều, Khoản, điểm",
    "type_4": "Chương, Mục, Điều, Khoản, điểm",
    "type_5": "Chương, Điều, Khoản, điểm",
    "type_6": "Điều, Khoản, điểm",
}

@dataclass
class Part:
    """ Simple base class design for a legal part """
    partType: str
    partId: str
    treeId: str
    text: str
    children: list[Part] = field(default_factory=list)

def visualize_part(part, level=1):
    """ Simple tree visualizer with level configuration """
    print(f"Item {part.partType} {part.partId}: {part.treeId}")
    print(f"Text: {part.text}")
    print(f"{len(part.children)} children: ")
    if len(part.children) > 0 and level > 0:
        for child_part in part.children:
            visualize_part(child_part, level-1)