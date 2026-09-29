#!/usr/bin/env python3
"""GIAI DOAN 1 - Sinh bo du lieu mau cho he thong canh bao tin nhan lua dao THCS.

Sinh ra 2 tep theo dung dac ta (Muc 4):
    * ``dataset_demo_60.jsonl``  - 60 tin nhan/doi thoai viet tay, dung de demo & kiem thu.
    * ``dataset_thcs_scam.jsonl`` - bo du lieu lon hon (mac dinh 1800 mau) sinh tu
      mau cau + tu dien khe cam (slot filling), co cau 40% an toan / 20% nghi van / 40% nguy hiem.

Dinh dang moi dong (JSONL):
    {"id": "MSG_0012", "text": "...", "label": 2, "label_name": "DANGEROUS",
     "category": "FAKE_PRIZE", "risk_entities": ["...", "..."]}

Cach dung::

    python data/generate_sample_dataset.py                 # sinh ca 2 tep
    python data/generate_sample_dataset.py --size 3000     # bo du lieu lon hon
    python data/generate_sample_dataset.py --demo-only
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import (  # noqa: E402
    CATEGORY_ACCOUNT_THREAT,
    CATEGORY_ADS_SPAM,
    CATEGORY_FAKE_PRIZE,
    CATEGORY_GAME_TOPUP,
    CATEGORY_IMPERSONATION_RELATIVE,
    CATEGORY_IMPERSONATION_TEACHER,
    CATEGORY_JOB_SCAM,
    CATEGORY_OTP_PHISHING,
    CATEGORY_PHISHING_LINK,
    CATEGORY_SAFE,
    CATEGORY_SUSPICIOUS_INVITE,
    DATASET_DEMO,
    DATASET_FULL,
    LEVEL_BY_LABEL,
)

# ---------------------------------------------------------------------------
# 1. TU DIEN KHE CAM (slots)
# ---------------------------------------------------------------------------
SLOTS: Dict[str, List[str]] = {
    "ten_thay": ["Nam", "Hùng", "Tuấn", "Minh", "Sơn", "Quang", "Dũng"],
    "ten_co": ["Lan", "Hoa", "Thu", "Hương", "Mai", "Trang", "Ngọc"],
    "mon": ["Toán", "Văn", "Anh", "Lý", "Hóa", "Sinh", "Sử", "Địa", "Tin", "thể dục"],
    "ten_ban": ["Bảo", "Khôi", "Linh", "An", "Duy", "Thảo", "Nhi", "Phúc"],
    "lop": ["6A1", "7A2", "8A3", "9A1", "6B", "7C", "8A", "9B"],
    "sdt": ["0987654321", "0912345678", "0355123456", "0978111222", "0333445566"],
    "tien": ["50k", "100k", "200k", "300k", "500k", "1 triệu", "2 triệu"],
    "the": ["Viettel", "Vinaphone", "Mobifone", "Garena", "Zing"],
    "game": ["Roblox", "Liên Quân", "Free Fire", "Play Together", "Blox Fruit", "PUBG Mobile"],
    "vat_pham": ["Robux", "kim cương", "quân huy", "skin SS", "vật phẩm VIP", "nick VIP"],
    "phan_thuong": ["iPhone 15", "xe đạp điện VinFast", "iPad", "laptop", "AirPods"],
    "link_xau": [
        "http://bit.ly/nhan-thuong-thcs",
        "https://robux-thcs.vip",
        "http://quatang-garena.top",
        "https://nhanqua-sukien.xyz",
        "http://trungthuong-2025.club",
        "https://facebook-xacminh.online",
    ],
    "link_lanh": ["https://hocmai.vn", "https://olm.vn", "https://quizizz.com/join"],
    "thoi_gian": ["5 phút", "10 phút", "30 phút", "1 tiếng", "hôm nay"],
    "trang": ["12", "25", "37", "48", "56", "72"],
    "bai": ["3", "5", "7", "9", "12"],
}


# Cac cach mo dau / ket thuc tin nhan thuong gap, giup du lieu da dang tu nhien hon.
OPENERS = ["", "", "", "Alo, ", "Này, ", "Ê, ", "Bạn ơi, ", "Em ơi, ", "Chào em, ", "Hi, "]
CLOSERS = ["", "", "", " nhé!", " nha.", " nhé bạn.", " ok?", " nhanh lên.", " cảm ơn nhé."]


def decorate(text: str, rng: random.Random) -> str:
    """Them loi chao / loi ket ngau nhien de tin nhan giong doi thuc hon."""
    opener = rng.choice(OPENERS)
    closer = rng.choice(CLOSERS)
    if opener:
        text = opener + text[0].lower() + text[1:]
    stripped = text.rstrip(" .!?").lower()
    # Tranh lap tro tu cuoi cau kieu "nhe nhe!".
    if closer and not stripped.endswith(("nhé", "nha", "nhá", "ạ", "nhé bạn", "ok")):
        text = text.rstrip(" .!") + closer
    return text


def fill(template: str, rng: random.Random) -> str:
    """Thay the cac khe {ten_thay}, {tien}... bang gia tri ngau nhien."""
    out = template
    for _ in range(6):  # du de xu ly cac khe long nhau
        changed = False
        for key, values in SLOTS.items():
            token = "{" + key + "}"
            while token in out:
                out = out.replace(token, rng.choice(values), 1)
                changed = True
        if not changed:
            break
    return out


# ---------------------------------------------------------------------------
# 2. 60 MAU VIET TAY (bo demo - Giai doan 1 cua dac ta)
#    Co cau: 24 an toan (40%) - 12 nghi van (20%) - 24 nguy hiem (40%)
# ---------------------------------------------------------------------------
SEED_SAFE: List[str] = [
    "Mai nhớ mang vở bài tập Toán nhé, cô kiểm tra 15 phút đấy!",
    "Tổ 2 trực nhật sáng mai, các bạn đến sớm 15 phút giúp mình với.",
    "Bài 5 trang 32 khó quá, tối nay gọi video giảng cho tớ với được không?",
    "Cô nhắc cả lớp nộp đề cương ôn tập Văn trước thứ 6 nhé.",
    "Mẹ đón con lúc 5h ở cổng trường, nhớ mang áo mưa.",
    "Chiều nay lớp mình sinh hoạt lớp, bạn nào chưa nộp sổ đầu bài thì nộp nhé.",
    "Mai mình đi đá bóng ở sân trường không? 4h chiều nhé.",
    "Bạn cho tớ mượn quyển sách giáo khoa Lý mai tớ trả.",
    "Thầy nhắc lớp 8A3 mai kiểm tra một tiết môn Hóa, ôn kỹ chương 2 nhé.",
    "Con ăn cơm trước đi, mẹ về muộn khoảng 7h.",
    "Nhóm mình họp làm bài thuyết trình Lịch sử lúc 8h tối trên Google Meet nha.",
    "Thời khóa biểu tuần sau đổi tiết 3 thứ 4 sang môn Tin học.",
    "Chúc mừng sinh nhật cậu nhé, mai tớ mang quà đến lớp!",
    "Mai mặc đồng phục thể dục nha các bạn, có tiết thể dục tiết 1.",
    "Bố nhắc con khóa cửa cẩn thận trước khi đi học.",
    "Tớ chép bài hộ cậu môn Địa rồi, mai qua lấy vở nhé.",
    "Lớp mình đăng ký thi học sinh giỏi Toán trước thứ 5, ai muốn thi thì báo lớp trưởng.",
    "Cả nhà nhớ 20/11 lớp mình chuẩn bị tiết mục văn nghệ nhé.",
    "Mai đi học mang theo compa và thước đo độ cho tiết Hình học.",
    "Tối nay có trận chung kết, xem xong rồi ngủ sớm nha!",
    "Cô giáo gửi link bài tập trên https://olm.vn, các em làm trước thứ 3.",
    "Mình quên mang bút, bạn cho mượn cây bút bi lúc vào lớp nhé.",
    "Ngày mai lớp lao động dọn vườn trường, các bạn mang theo găng tay.",
    "Bạn ơi, hôm nay học bài nào môn Anh thế? Tớ nghỉ ốm chưa chép kịp.",
]

SEED_SUSPICIOUS: List[str] = [
    "Mời bạn tham gia nhóm học tiếng Anh online miễn phí, vào nhóm để nhận tài liệu nhé.",
    "Bạn ơi vào nhóm này chơi cho vui, nhóm kín toàn học sinh thôi: https://zalo.me/g/abcxyz",
    "Sale sốc cuối tuần, giày thể thao giá chỉ từ 99k, inbox để đặt hàng nha!",
    "Shop mình đang khuyến mãi phụ kiện điện thoại, giảm giá 50% cho học sinh.",
    "Tham gia group Discord của server game mới, có nhiều bạn cùng tuổi lắm.",
    "Bạn có muốn nhận tài liệu ôn thi miễn phí không? Để lại số điện thoại mình gửi.",
    "Mình là admin fanpage, bạn tham gia minigame của trang để nhận quà nhé.",
    "Nhóm chat mới của lớp đây, mọi người vào đi: link trong bio.",
    "Xả kho balo học sinh, số lượng có hạn, nhắn tin để được tư vấn.",
    "Bạn được mời dùng thử ứng dụng học tập mới, tải tại link sau nhé.",
    "Có ai muốn mua lại tài khoản game giá rẻ không, mình nhượng lại.",
    "Mình lập nhóm ôn thi học kỳ, bạn cho mình xin Zalo để thêm vào nhé.",
]

SEED_DANGEROUS: List[Tuple[str, str]] = [
    ("Thầy Nam thể dục đây, nạp hộ thầy 2 thẻ Viettel 100k vào số này gấp, mai lên lớp thầy gửi lại.", CATEGORY_IMPERSONATION_TEACHER),
    ("Cô Lan chủ nhiệm đây, cô đang họp không rút tiền được, em chuyển giúp cô 500k vào số tài khoản 19001234567, mai cô trả.", CATEGORY_IMPERSONATION_TEACHER),
    ("Nhà trường thông báo khẩn: phụ huynh chuyển ngay 300k phí hồ sơ vào tài khoản dưới đây trong hôm nay.", CATEGORY_IMPERSONATION_TEACHER),
    ("Thầy Hùng đây, em mua giúp thầy 3 thẻ cào 200k rồi chụp mã gửi thầy nhé, đừng nói với bố mẹ.", CATEGORY_IMPERSONATION_TEACHER),
    ("Mẹ đây, mẹ đổi số mới, con chuyển gấp 2 triệu vào số tài khoản này giúp mẹ nhé.", CATEGORY_IMPERSONATION_RELATIVE),
    ("Tao là Bảo bạn cùng lớp, nick cũ của tao bị hack rồi, cho tao mượn tạm 300k gấp nhé.", CATEGORY_IMPERSONATION_RELATIVE),
    ("Minh đây, điện thoại mình hết tiền, bạn nạp giúp mình cái thẻ 100k mai mình trả.", CATEGORY_IMPERSONATION_RELATIVE),
    ("Nhập mã OTP vừa gửi về điện thoại để nhận 1000 Robux miễn phí tại web robux-thcs.vip", CATEGORY_OTP_PHISHING),
    ("Bạn vừa đăng nhập tài khoản ở thiết bị lạ, đọc mã xác minh 6 số vừa gửi để khóa lại ngay.", CATEGORY_OTP_PHISHING),
    ("Cho anh xin mật khẩu Facebook của em để anh sửa lỗi hiển thị giúp nhé.", CATEGORY_OTP_PHISHING),
    ("Đăng nhập bằng tài khoản Garena tại trang nay-nhan-qua.top để nhận quân huy miễn phí nhé.", CATEGORY_OTP_PHISHING),
    ("Sự kiện tri ân Roblox: nạp 100k tặng 10000 Robux, chỉ trong hôm nay, nhắn tin ngay để nhận!", CATEGORY_GAME_TOPUP),
    ("Mình có tool hack kim cương Free Fire, chuyển 50k mình gửi cho, nhanh kẻo hết!", CATEGORY_GAME_TOPUP),
    ("Nhận skin SS miễn phí Liên Quân, chỉ cần cho mượn nick 10 phút thôi.", CATEGORY_GAME_TOPUP),
    ("Chúc mừng bạn đã trúng thưởng iPhone 15 từ chương trình tri ân. Đóng 350k phí vận chuyển để nhận quà.", CATEGORY_FAKE_PRIZE),
    ("Bạn là người may mắn trúng 1 xe đạp điện VinFast. Click vào link sau để xác nhận: http://bit.ly/nhan-thuong-thcs", CATEGORY_FAKE_PRIZE),
    ("Số điện thoại của bạn đã trúng giải nhất chương trình quay số. Truy cập trungthuong-2025.club để nhận thưởng.", CATEGORY_FAKE_PRIZE),
    ("Tao có ảnh của mày, nếu không chuyển 500k trong 30 phút tao sẽ tung lên group lớp.", CATEGORY_ACCOUNT_THREAT),
    ("Nick của mày đang trong tay tao. Muốn lấy lại thì nạp 200k thẻ Viettel, đừng báo bố mẹ.", CATEGORY_ACCOUNT_THREAT),
    ("Tài khoản Facebook của bạn sẽ bị khóa vĩnh viễn trong 24h, xác minh ngay tại facebook-xacminh.online", CATEGORY_ACCOUNT_THREAT),
    ("Cảnh báo: tài khoản Zalo của bạn bị đăng nhập lạ, bấm vào link này để bảo vệ ngay lập tức.", CATEGORY_PHISHING_LINK),
    ("Xem ảnh lớp mình đi chơi nè, tải về tại http://192.168.10.5/anh-lop.apk nhé.", CATEGORY_PHISHING_LINK),
    ("Tuyển cộng tác viên là học sinh, làm nhiệm vụ online kiếm 500k mỗi ngày, đặt cọc 200k để nhận việc.", CATEGORY_JOB_SCAM),
    ("Việc nhẹ lương cao cho học sinh cấp 2, chỉ cần like dạo, hoa hồng 100k/buổi, nhắn tin ngay.", CATEGORY_JOB_SCAM),
]

# ---------------------------------------------------------------------------
# 3. MAU CAU DE SINH BO DU LIEU LON
# ---------------------------------------------------------------------------
TEMPLATES_SAFE: List[str] = [
    "Mai nhớ mang vở bài tập {mon} nhé, cô kiểm tra 15 phút đấy.",
    "Bài {bai} trang {trang} khó quá, tối nay cậu giảng cho tớ với.",
    "Tổ trực nhật sáng mai đến sớm {thoi_gian} giúp mình nhé.",
    "Thầy {ten_thay} nhắc lớp {lop} mai kiểm tra một tiết môn {mon}.",
    "Cô {ten_co} yêu cầu nộp đề cương môn {mon} trước thứ 6.",
    "{ten_ban} ơi, cho tớ mượn sách giáo khoa {mon} mai tớ trả nhé.",
    "Mẹ đón con lúc 5h ở cổng trường, nhớ mang áo mưa nha.",
    "Nhóm mình họp làm bài thuyết trình môn {mon} lúc 8h tối nhé.",
    "Chiều nay lớp {lop} sinh hoạt lớp, bạn nào chưa nộp sổ thì nộp.",
    "Mai mình đi đá bóng không {ten_ban}? 4h chiều ở sân trường.",
    "Cô gửi link bài tập môn {mon} trên {link_lanh}, các em làm trước thứ 3.",
    "Thời khóa biểu tuần sau đổi tiết 3 thứ 4 sang môn {mon}.",
    "Chúc mừng sinh nhật {ten_ban} nhé, mai tớ mang quà đến lớp!",
    "Bố nhắc con khóa cửa cẩn thận trước khi đi học nhé.",
    "Tớ chép bài hộ cậu môn {mon} rồi, mai qua lấy vở nha.",
    "Lớp {lop} đăng ký thi học sinh giỏi môn {mon} trước thứ 5 nhé.",
    "Mai đi học mang theo compa và thước cho tiết {mon}.",
    "{ten_ban} ơi hôm nay học bài nào môn {mon} thế, tớ nghỉ ốm chưa chép kịp.",
    "Con ăn cơm trước đi, mẹ về muộn khoảng 7h tối.",
    "Ngày mai lớp lao động dọn vườn trường, các bạn mang găng tay nhé.",
]

TEMPLATES_SUSPICIOUS: List[str] = [
    "Mời bạn tham gia nhóm học {mon} online miễn phí, vào nhóm để nhận tài liệu nhé.",
    "Vào nhóm này chơi cho vui nha, nhóm kín toàn học sinh thôi: {link_lanh}",
    "Sale sốc cuối tuần, đồ dùng học tập giá chỉ từ 99k, inbox để đặt hàng!",
    "Shop đang khuyến mãi phụ kiện {game}, giảm giá 50% cho học sinh.",
    "Tham gia group Discord của server {game} mới, nhiều bạn cùng tuổi lắm.",
    "Bạn muốn nhận tài liệu ôn thi môn {mon} miễn phí không? Để lại số điện thoại mình gửi.",
    "Mình là admin fanpage, bạn tham gia minigame của trang để nhận quà nhé.",
    "Nhóm chat mới của lớp {lop} đây, mọi người vào đi nhé.",
    "Có ai muốn mua lại tài khoản {game} giá rẻ không, mình nhượng lại.",
    "Bạn được mời dùng thử ứng dụng học tập mới, tải ở link trong phần giới thiệu.",
    "Mình lập nhóm ôn thi học kỳ, cho mình xin Zalo để thêm vào nhé.",
    "Xả kho balo học sinh, số lượng có hạn, nhắn tin để được tư vấn giá.",
    "Bạn ơi, có ai tặng bạn thẻ {the} {tien} bao giờ chưa? Nhóm mình đang có chương trình đó.",
    "Đăng ký nhận vé xem phim miễn phí cho học sinh lớp {lop}, để lại tên và số điện thoại nhé.",
    "Nhóm mua chung đồ dùng học tập môn {mon} đây, bạn tham gia cho rẻ nhé.",
    "Ai cần gia sư môn {mon} giá rẻ không, inbox mình gửi thông tin.",
    "Mình bán lại vật phẩm {vat_pham} game {game} giá mềm, ai cần thì nhắn.",
    "Tham gia khảo sát ngắn về game {game} để nhận thẻ quà tặng nhé.",
    "Bạn được tặng 1 khóa học {mon} online, đăng ký tại link nhóm nha.",
    "Group bàn luận {game} của trường mình mới lập, vào cho vui nhé.",
    "Có bạn nào muốn đổi vật phẩm {game} không, mình đổi công bằng.",
    "Nhắn tin để nhận bảng giá đồ dùng học tập cho lớp {lop} nhé.",
]

TEMPLATES_DANGEROUS: List[Tuple[str, str]] = [
    ("Thầy {ten_thay} môn {mon} đây, nạp hộ thầy 2 thẻ {the} {tien} vào số {sdt} gấp, mai thầy gửi lại.", CATEGORY_IMPERSONATION_TEACHER),
    ("Cô {ten_co} chủ nhiệm đây, cô đang họp không rút tiền được, em chuyển giúp cô {tien} vào số tài khoản 19001234567 nhé.", CATEGORY_IMPERSONATION_TEACHER),
    ("Thầy {ten_thay} đây, em mua giúp thầy 3 thẻ cào {tien} rồi chụp mã gửi thầy, đừng nói với bố mẹ nhé.", CATEGORY_IMPERSONATION_TEACHER),
    ("Nhà trường thông báo khẩn: phụ huynh lớp {lop} chuyển {tien} phí hồ sơ trong hôm nay vào số {sdt}.", CATEGORY_IMPERSONATION_TEACHER),
    ("Mẹ đây, mẹ đổi số mới, con chuyển gấp {tien} vào số tài khoản này giúp mẹ.", CATEGORY_IMPERSONATION_RELATIVE),
    ("Tao là {ten_ban} bạn cùng lớp, nick cũ của tao bị hack rồi, cho tao mượn tạm {tien} gấp nhé.", CATEGORY_IMPERSONATION_RELATIVE),
    ("{ten_ban} đây, điện thoại mình hết tiền, bạn nạp giúp mình thẻ {the} {tien} mai mình trả.", CATEGORY_IMPERSONATION_RELATIVE),
    ("Nhập mã OTP vừa gửi về điện thoại để nhận {vat_pham} miễn phí tại {link_xau}", CATEGORY_OTP_PHISHING),
    ("Tài khoản {game} của bạn vừa đăng nhập ở thiết bị lạ, đọc mã xác minh 6 số vừa gửi để khóa lại ngay.", CATEGORY_OTP_PHISHING),
    ("Cho anh xin mật khẩu tài khoản {game} của em để anh sửa lỗi giúp nhé.", CATEGORY_OTP_PHISHING),
    ("Đăng nhập bằng tài khoản Facebook tại {link_xau} để nhận {vat_pham} miễn phí.", CATEGORY_OTP_PHISHING),
    ("Sự kiện tri ân {game}: nạp {tien} tặng 10000 {vat_pham}, chỉ trong {thoi_gian}, nhắn tin ngay!", CATEGORY_GAME_TOPUP),
    ("Mình có tool hack {vat_pham} {game}, chuyển {tien} mình gửi cho, nhanh kẻo hết.", CATEGORY_GAME_TOPUP),
    ("Nhận {vat_pham} miễn phí game {game}, chỉ cần cho mượn nick {thoi_gian} thôi.", CATEGORY_GAME_TOPUP),
    ("Nạp {tien} tặng gấp đôi {vat_pham} cho game {game}, chuyển vào số {sdt} nhé.", CATEGORY_GAME_TOPUP),
    ("Chúc mừng bạn đã trúng thưởng {phan_thuong} từ chương trình tri ân. Đóng {tien} phí vận chuyển để nhận quà.", CATEGORY_FAKE_PRIZE),
    ("Bạn là người may mắn trúng 1 {phan_thuong}. Click vào link sau để xác nhận: {link_xau}", CATEGORY_FAKE_PRIZE),
    ("Số điện thoại của bạn đã trúng giải nhất chương trình quay số, truy cập {link_xau} để nhận thưởng.", CATEGORY_FAKE_PRIZE),
    ("Tao có ảnh của mày, nếu không chuyển {tien} trong {thoi_gian} tao sẽ tung lên group lớp {lop}.", CATEGORY_ACCOUNT_THREAT),
    ("Nick {game} của mày đang trong tay tao, muốn lấy lại thì nạp {tien} thẻ {the}, đừng báo bố mẹ.", CATEGORY_ACCOUNT_THREAT),
    ("Tài khoản của bạn sẽ bị khóa vĩnh viễn trong {thoi_gian}, xác minh ngay tại {link_xau}", CATEGORY_ACCOUNT_THREAT),
    ("Cảnh báo bảo mật: tài khoản Zalo bị đăng nhập lạ, bấm vào {link_xau} để bảo vệ ngay.", CATEGORY_PHISHING_LINK),
    ("Xem ảnh lớp {lop} đi chơi nè, tải về tại http://192.168.10.5/anh-lop.apk nhé.", CATEGORY_PHISHING_LINK),
    ("Bấm ngay vào {link_xau} để nhận {vat_pham} trước khi hết hạn trong {thoi_gian}.", CATEGORY_PHISHING_LINK),
    ("Tuyển cộng tác viên là học sinh, làm nhiệm vụ online kiếm {tien} mỗi ngày, đặt cọc {tien} để nhận việc.", CATEGORY_JOB_SCAM),
    ("Việc nhẹ lương cao cho học sinh cấp 2, chỉ cần like dạo, hoa hồng {tien} một buổi, nhắn tin ngay.", CATEGORY_JOB_SCAM),
]

# Bien the cach go cua hoc sinh: khong dau / viet tat -> giup mo hinh ben hon.
NO_DIACRITIC_RATIO = 0.25


def strip_diacritics(text: str) -> str:
    from app.text_utils import fold

    return fold(text)


def extract_risk_entities(text: str) -> List[str]:
    """Trich cac cum tu rui ro bang chinh bo luat cua Module 2 (phuc vu cot `risk_entities`).

    Luu y: `label` luon la nhan *goc* tu mau cau (ground truth), khong lay tu mo hinh,
    nen viec dung bo luat o day khong lam ro ri nhan huan luyen.
    """
    from app.classifier import analyze

    result = analyze(text, use_ml=False)
    return result.highlight_words[:4]


def _build_records(
    items: Sequence[Tuple[str, int, str, str]], rng: random.Random, start_index: int = 1
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for offset, (text, label, category, template_id) in enumerate(items, start=start_index):
        if rng.random() < NO_DIACRITIC_RATIO:
            text = strip_diacritics(text)
        records.append(
            {
                "id": f"MSG_{offset:04d}",
                "text": text,
                "label": label,
                "label_name": LEVEL_BY_LABEL[label],
                "category": category,
                "template_id": template_id,
                "risk_entities": extract_risk_entities(text),
            }
        )
    return records


def build_demo_set(rng: random.Random) -> List[Dict[str, object]]:
    """60 tin nhan viet tay: 24 an toan / 12 nghi van / 24 nguy hiem."""
    items: List[Tuple[str, int, str, str]] = []
    items += [(t, 0, CATEGORY_SAFE, f"SEED_S{i:02d}") for i, t in enumerate(SEED_SAFE)]
    items += [
        (t, 1, CATEGORY_SUSPICIOUS_INVITE if "nhóm" in t or "group" in t else CATEGORY_ADS_SPAM, f"SEED_W{i:02d}")
        for i, t in enumerate(SEED_SUSPICIOUS)
    ]
    items += [(t, 2, cat, f"SEED_D{i:02d}") for i, (t, cat) in enumerate(SEED_DANGEROUS)]
    rng.shuffle(items)
    return _build_records(items, rng)


def build_full_set(size: int, rng: random.Random) -> List[Dict[str, object]]:
    """Bo du lieu lon sinh tu mau cau, giu dung co cau 40% / 20% / 40%."""
    n_safe = round(size * 0.4)
    n_susp = round(size * 0.2)
    n_danger = size - n_safe - n_susp

    items: List[Tuple[str, int, str, str]] = []
    seen: set[str] = set()

    def add(text: str, label: int, category: str, template_id: str) -> bool:
        key = text.lower()
        if key in seen:
            return False
        seen.add(key)
        items.append((text, label, category, template_id))
        return True

    # Giu lai toan bo mau viet tay trong bo lon de dam bao chat luong nen.
    for i, text in enumerate(SEED_SAFE):
        add(text, 0, CATEGORY_SAFE, f"SEED_S{i:02d}")
    for i, text in enumerate(SEED_SUSPICIOUS):
        category = CATEGORY_SUSPICIOUS_INVITE if "nhóm" in text or "group" in text else CATEGORY_ADS_SPAM
        add(text, 1, category, f"SEED_W{i:02d}")
    for i, (text, cat) in enumerate(SEED_DANGEROUS):
        add(text, 2, cat, f"SEED_D{i:02d}")

    def fill_bucket(target: int, label: int, templates: Sequence[object], prefix: str) -> None:
        current = sum(1 for _, lab, _, _ in items if lab == label)
        guard = 0
        template_list = list(templates)
        while current < target and guard < target * 80:
            guard += 1
            index = rng.randrange(len(template_list))
            choice = template_list[index]
            if isinstance(choice, tuple):
                template, category = choice
            else:
                template, category = choice, (CATEGORY_SAFE if label == 0 else CATEGORY_SUSPICIOUS_INVITE)
            text = decorate(fill(template, rng), rng)
            if label == 1 and ("sale" in text.lower() or "khuyến mãi" in text.lower() or "xả kho" in text.lower()):
                category = CATEGORY_ADS_SPAM
            if add(text, label, category, f"{prefix}{index:02d}"):
                current += 1

    fill_bucket(n_safe, 0, TEMPLATES_SAFE, "TPL_S")
    fill_bucket(n_susp, 1, TEMPLATES_SUSPICIOUS, "TPL_W")
    fill_bucket(n_danger, 2, TEMPLATES_DANGEROUS, "TPL_D")

    rng.shuffle(items)
    return _build_records(items, rng)


def write_jsonl(records: Iterable[Dict[str, object]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def summarize(records: Sequence[Dict[str, object]]) -> str:
    total = len(records)
    counts: Dict[str, int] = {}
    for record in records:
        counts[str(record["label_name"])] = counts.get(str(record["label_name"]), 0) + 1
    parts = [f"{name}: {n} ({n / total:.0%})" for name, n in sorted(counts.items())]
    return f"{total} mẫu | " + " | ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sinh bo du lieu mau tin nhan lua dao cho hoc sinh THCS")
    parser.add_argument("--size", type=int, default=1800, help="So mau cua bo du lieu lon (mac dinh 1800)")
    parser.add_argument("--seed", type=int, default=2025, help="Seed ngau nhien de tai lap ket qua")
    parser.add_argument("--out", type=Path, default=DATASET_FULL, help="Duong dan bo du lieu lon")
    parser.add_argument("--demo-out", type=Path, default=DATASET_DEMO, help="Duong dan bo demo 60 mau")
    parser.add_argument("--demo-only", action="store_true", help="Chi sinh bo demo 60 mau")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    demo = build_demo_set(rng)
    write_jsonl(demo, args.demo_out)
    print(f"[demo] {args.demo_out}: {summarize(demo)}")

    if not args.demo_only:
        rng_full = random.Random(args.seed + 1)
        full = build_full_set(args.size, rng_full)
        write_jsonl(full, args.out)
        print(f"[full] {args.out}: {summarize(full)}")


if __name__ == "__main__":
    main()
