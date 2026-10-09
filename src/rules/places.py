"""Luật về địa danh: tên tỉnh / thành phố và cách viết khác nhau của cùng một nơi."""
import re

provinces = [
    "Hà Nội", "Hồ Chí Minh", "TP.HCM", "TPHCM", "Sài Gòn", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Huế", "Thừa Thiên Huế",
    "Lai Châu", "Điện Biên", "Sơn La", "Lạng Sơn", "Quảng Ninh", "Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Cao Bằng",
    "Tuyên Quang", "Lào Cai", "Thái Nguyên", "Phú Thọ", "Bắc Ninh", "Hưng Yên", "Ninh Bình", "Quảng Trị",
    "Quảng Ngãi", "Gia Lai", "Khánh Hòa", "Lâm Đồng", "Đắk Lắk", "Đồng Nai", "Tây Ninh", "Vĩnh Long", "Đồng Tháp",
    "Cà Mau", "An Giang", "Hà Giang", "Yên Bái", "Bắc Kạn", "Bắc Giang", "Vĩnh Phúc", "Hải Dương", "Hà Nam",
    "Nam Định", "Thái Bình", "Quảng Bình", "Quảng Nam", "Kon Tum", "Bình Định", "Phú Yên", "Ninh Thuận",
    "Bình Thuận", "Đắk Nông", "Bình Phước", "Bình Dương", "Bà Rịa - Vũng Tàu", "Bà Rịa Vũng Tàu", "Vũng Tàu",
    "Long An", "Tiền Giang", "Bến Tre", "Trà Vinh", "Hậu Giang", "Sóc Trăng", "Bạc Liêu", "Kiên Giang",
]
# Tên dễ nhầm với từ thường ("hòa bình"): chỉ nhận khi có tiền tố "tỉnh" / "thành phố"
ambiguous_provinces = ["Hòa Bình"]

def build_province_pattern() -> re.Pattern:
    """Nhóm 1: tên tỉnh thông thường; nhóm 2: tên dễ nhầm, chỉ nhận khi đi sau "tỉnh" / "thành phố"."""
    # Tên dài xếp trước để "Bà Rịa - Vũng Tàu" được khớp trước "Vũng Tàu"
    common_names = []
    for province in sorted(provinces, key=len, reverse=True):
        common_names.append(re.escape(province))

    ambiguous_names = []
    for province in ambiguous_provinces:
        ambiguous_names.append(re.escape(province))

    common_part = r"(?<!\w)(" + "|".join(common_names) + r")(?!\w)"
    ambiguous_part = r"|(?:tỉnh|thành phố)\s+(" + "|".join(ambiguous_names) + r")(?!\w)"
    return re.compile(common_part + ambiguous_part, re.UNICODE)


province_pattern = build_province_pattern()

# Cách viết khác -> tên chuẩn
province_canonical_names = {"TP.HCM": "Hồ Chí Minh", "TPHCM": "Hồ Chí Minh", "Sài Gòn": "Hồ Chí Minh",
                            "Thừa Thiên Huế": "Huế", "Bà Rịa Vũng Tàu": "Bà Rịa - Vũng Tàu",
                            "Vũng Tàu": "Bà Rịa - Vũng Tàu"}
