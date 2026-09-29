"""Tien ich xu ly van ban tieng Viet dung chung cho toan he thong.

Diem mau chot: moi luat nhan dien (Module 2) deu duoc viet bang tieng Viet
*khong dau* va doi chieu voi ban "fold" cua tin nhan. Nho vay mot cau viet
"nap ho thay 2 the viettel" va "nạp hộ thầy 2 thẻ Viettel" deu khop cung mot luat.

De phan XAI (giai thich) tra ve dung nguyen van doan trich trong tin nhan goc,
ham :func:`fold_with_map` tra ve them bang anh xa chi so: ``index_map[i]`` la vi tri
trong chuoi goc cua ky tu thu ``i`` trong chuoi da fold.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Sequence, Tuple

__all__ = [
    "fold",
    "fold_with_map",
    "deleet",
    "dense",
    "restore_diacritics",
    "tokenize_for_display",
    "word_count",
    "map_span",
]

# Ky tu dac biet thuong duoc ke gian lan chen vao de vuot bo loc tu khoa.
_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)

# Bang thay the kieu "leet" (0tp -> otp, m4t kh4u -> mat khau).
_LEET_TABLE = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}


def _fold_char(ch: str) -> str:
    """Chuyen 1 ky tu tieng Viet ve ASCII thuong (giu nguyen do dai 0 hoac 1)."""
    if ch in ("đ", "Đ"):
        return "d"
    decomposed = unicodedata.normalize("NFD", ch)
    base = "".join(c for c in decomposed if not unicodedata.combining(c))
    return base.lower()


def fold_with_map(text: str) -> Tuple[str, List[int]]:
    """Fold van ban ve dang ASCII thuong, khoang trang chuan hoa.

    Returns:
        ``(folded, index_map)`` voi ``index_map[i]`` la chi so trong ``text`` goc
        cua ky tu ``folded[i]``.
    """
    text = text.translate(_ZERO_WIDTH)
    out_chars: List[str] = []
    index_map: List[int] = []
    pending_space = False

    for idx, ch in enumerate(text):
        if ch.isspace():
            # Gop moi cum khoang trang / xuong dong thanh 1 dau cach.
            pending_space = bool(out_chars)
            continue
        folded = _fold_char(ch)
        if not folded:
            continue
        if pending_space:
            out_chars.append(" ")
            index_map.append(idx)
            pending_space = False
        for sub in folded:
            out_chars.append(sub)
            index_map.append(idx)

    return "".join(out_chars), index_map


def fold(text: str) -> str:
    """Ban rut gon cua :func:`fold_with_map` khi khong can bang anh xa."""
    return fold_with_map(text)[0]


def _should_deleet(token: str) -> bool:
    """Chi bien doi leet cho token *chu la chinh* de khong pha so/URL.

    ``0tp`` (1 so le loi giua chu) -> doi thanh ``otp``.
    ``100k``, ``192.168.10.5``, ``http://...`` -> giu nguyen.
    """
    if any(c in token for c in ":/@"):
        return False
    letters = sum(c.isalpha() for c in token)
    digits = sum(c.isdigit() for c in token)
    if letters == 0 or digits == 0 or letters < digits:
        return False
    # Che leet that su chi chen *mot* chu so le loi giua cac chu cai.
    return all(len(run) == 1 for run in re.findall(r"\d+", token))


def deleet(folded: str) -> str:
    """Khu che kieu leet nhung *giu nguyen do dai chuoi* de bang anh xa con dung."""
    out: List[str] = []
    for token in re.split(r"(\s+)", folded):
        if token.strip() and _should_deleet(token):
            out.append("".join(_LEET_TABLE.get(c, c) for c in token))
        else:
            out.append(token)
    return "".join(out)


def dense(folded: str) -> str:
    """Bo het khoang trang / dau cham cau: bat cac chieu tro giãn cach ("n a p t h e")."""
    return re.sub(r"[^a-z0-9]+", "", folded)


def map_span(folded: str, index_map: Sequence[int], start: int, end: int, original: str) -> str:
    """Lay lai doan van ban *goc* tuong ung voi khoang ``[start, end)`` tren ban fold.

    Khoang trang thua o hai dau duoc cat bo truoc khi anh xa, vi ky tu space trong
    ban fold tro toi vi tri cua ky tu *ke tiep* trong van ban goc.
    """
    end = min(end, len(index_map), len(folded))
    while start < end and folded[start].isspace():
        start += 1
    while end > start and folded[end - 1].isspace():
        end -= 1
    if start >= end or start >= len(index_map):
        return ""
    orig_start = index_map[start]
    orig_end = index_map[end - 1] + 1
    return original[orig_start:orig_end].strip()


# ---------------------------------------------------------------------------
# Khoi phuc dau tieng Viet (phuc vu hien thi `normalized_text` o Module 1)
# ---------------------------------------------------------------------------
# Day la bo tu dien theo *ngu canh lua dao hoc duong*, khong phai bo khoi phuc
# dau tong quat. Tu nao khong co trong tu dien se duoc giu nguyen.
_DIACRITIC_LEXICON: Dict[str, str] = {
    # Xung ho / truong lop
    "thay": "thầy", "co": "cô", "em": "em", "ban": "bạn", "con": "con",
    "me": "mẹ", "bo": "bố", "ba": "ba", "chi": "chị", "anh": "anh",
    "chu": "chú", "bac": "bác", "truong": "trường", "lop": "lớp",
    "hoc": "học", "sinh": "sinh", "bai": "bài", "tap": "tập", "kiem": "kiểm",
    "tra": "tra", "diem": "điểm", "sach": "sách", "vo": "vở", "gio": "giờ",
    "chu nhiem": "chủ nhiệm", "the duc": "thể dục", "truc nhat": "trực nhật",
    "hoc sinh": "học sinh", "phu huynh": "phụ huynh", "giao vien": "giáo viên",
    # Tien bac / the cao
    "nap": "nạp", "the": "thẻ", "tien": "tiền", "chuyen": "chuyển",
    "khoan": "khoản", "tai": "tài", "ngan": "ngân", "hang": "hàng",
    "ma": "mã", "so": "số", "phi": "phí", "cuoc": "cước", "muon": "mượn",
    "vay": "vay", "gui": "gửi", "lai": "lại", "ho": "hộ", "giup": "giúp",
    "nghin": "nghìn", "trieu": "triệu", "dong": "đồng",
    # Thoi gian / thuc giuc
    "gap": "gấp", "ngay": "ngay", "nhanh": "nhanh", "lien": "liền",
    "khan": "khẩn", "cap": "cấp", "truoc": "trước", "sau": "sau",
    "hom": "hôm", "mai": "mai", "toi": "tối", "sang": "sáng", "chieu": "chiều",
    "phut": "phút", "trong": "trong", "han": "hạn", "cuoi": "cuối",
    # Game / qua tang
    "mien": "miễn", "tang": "tặng", "qua": "quà", "trung": "trúng",
    "thuong": "thưởng", "nhan": "nhận", "kim": "kim", "cuong": "cương",
    "vat": "vật", "pham": "phẩm", "su": "sự", "kien": "kiện",
    "mien phi": "miễn phí", "trung thuong": "trúng thưởng",
    # Tai khoan / de doa
    "mat": "mật", "khau": "khẩu", "mat khau": "mật khẩu", "bao": "bảo",
    "xac": "xác", "minh": "minh", "khoa": "khóa", "doa": "dọa", "de": "đe",
    "de doa": "đe dọa", "phat": "phát", "tan": "tán", "rieng": "riêng",
    "tu": "tư", "canh": "cảnh", "giac": "giác", "lua": "lừa", "dao": "đảo",
    "chiem": "chiếm", "doat": "đoạt", "danh": "đánh", "an cap": "ăn cắp",
    # Dong tu / tu noi thong dung
    "lam": "làm", "khong": "không", "co": "có", "duoc": "được", "vao": "vào",
    "ra": "ra", "len": "lên", "xuong": "xuống", "voi": "với", "cho": "cho",
    "cua": "của", "nay": "này", "kia": "kia", "day": "đây", "do": "đó",
    "neu": "nếu", "thi": "thì", "va": "và", "hay": "hãy", "dung": "đừng",
    "phai": "phải", "can": "cần", "biet": "biết", "noi": "nói", "nho": "nhờ",
    "xem": "xem", "thu": "thử", "dang": "đang", "roi": "rồi", "nua": "nữa",
    "nhe": "nhé", "a": "ạ", "oi": "ơi", "di": "đi", "duong": "đường",
    "link": "link", "tren": "trên", "duoi": "dưới", "moi": "mời",
    "nhom": "nhóm", "dien": "điện", "thoai": "thoại", "dien thoai": "điện thoại",
    "xe dap dien": "xe đạp điện", "may": "may", "man": "mắn",
    "may man": "may mắn", "khach": "khách", "trong": "trong",
}

# Cum tu 2-3 tieng duoc uu tien khop truoc tu don.
_PHRASE_LEXICON = {k: v for k, v in _DIACRITIC_LEXICON.items() if " " in k}
_MAX_PHRASE_LEN = max((len(k.split()) for k in _PHRASE_LEXICON), default=1)


def restore_diacritics(folded_text: str) -> str:
    """Khoi phuc dau tieng Viet dua tren tu dien ngu canh lua dao.

    Chi mang tinh *hien thi* cho hoc sinh doc lai cho de hieu. Neu tin nhan goc
    da co dau thi ham nay khong duoc goi (xem :mod:`app.preprocessor`).
    """
    tokens = folded_text.split()
    out: List[str] = []
    i = 0
    while i < len(tokens):
        matched = False
        for span in range(min(_MAX_PHRASE_LEN, len(tokens) - i), 1, -1):
            phrase = " ".join(tokens[i : i + span])
            if phrase in _PHRASE_LEXICON:
                out.append(_PHRASE_LEXICON[phrase])
                i += span
                matched = True
                break
        if matched:
            continue
        token = tokens[i]
        core = token.strip(".,!?;:()[]\"'")
        suffix = token[len(core) :] if core else ""
        prefix_len = len(token) - len(token.lstrip(".,!?;:()[]\"'"))
        prefix = token[:prefix_len]
        out.append(prefix + _DIACRITIC_LEXICON.get(core, core) + suffix)
        i += 1
    return " ".join(out)


def tokenize_for_display(text: str) -> str:
    """Tach dau cau ra khoi tu (theo dung dinh dang `normalized_text` trong dac ta)."""
    spaced = re.sub(r"([.,!?;:])(?=\s|$)", r" \1", text)
    return re.sub(r"\s+", " ", spaced).strip()


def word_count(text: str) -> int:
    return len([t for t in re.split(r"\s+", text.strip()) if t])
