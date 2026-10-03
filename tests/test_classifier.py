"""Kiem thu Module 2 - phan loai rui ro va giai thich (XAI)."""

import pytest

from app.classifier import analyze
from app.config import (
    CATEGORY_ACCOUNT_THREAT,
    CATEGORY_FAKE_PRIZE,
    CATEGORY_IMPERSONATION_TEACHER,
    CATEGORY_OTP_PHISHING,
    LEVEL_DANGEROUS,
    LEVEL_SAFE,
    LEVEL_SUSPICIOUS,
)

DANGEROUS_MESSAGES = [
    "Thầy Nam thể dục đây, nạp hộ thầy 2 thẻ Viettel 100k vào số này gấp.",
    "thay nam the duc day, nap ho thay 2 the viettel 100k vao so nay gap",
    "Nhập mã OTP vừa gửi về điện thoại để nhận 1000 Robux miễn phí tại robux-thcs.vip",
    "Bạn trúng 1 xe đạp điện VinFast, click http://bit.ly/nhan-thuong-thcs để xác nhận.",
    "Tao có ảnh của mày, không chuyển 500k tao sẽ tung lên group lớp.",
    "Mẹ đây, mẹ đổi số mới, con chuyển gấp 2 triệu vào số tài khoản này giúp mẹ.",
    "Cho anh xin mật khẩu Facebook của em để anh sửa lỗi giúp nhé.",
    "Tuyển CTV học sinh làm nhiệm vụ online kiếm 500k/ngày, đặt cọc 200k để nhận việc.",
]

SAFE_MESSAGES = [
    "Mai nhớ mang vở bài tập Toán nhé, cô kiểm tra 15 phút đấy!",
    "Mẹ đón con lúc 5h ở cổng trường, nhớ mang áo mưa.",
    "Bạn cho tớ mượn quyển sách giáo khoa Lý mai tớ trả.",
    "Tổ 2 trực nhật sáng mai, các bạn đến sớm 15 phút giúp mình với.",
    "Cô gửi link bài tập trên https://olm.vn, các em làm trước thứ 3.",
    # Thay co tu xung roi giao bai tap - khong hoi tien/OTP/link -> khong duoc bao nham.
    "cô my đây con làm bài tập nhé",
    "co my day con lam bai tap nhe",
    "Thầy Nam toán đây, các em ôn tập chương 2 để mai kiểm tra 15 phút.",
]


@pytest.mark.parametrize("message", DANGEROUS_MESSAGES)
def test_dangerous_messages_are_flagged(message):
    result = analyze(message, use_ml=False)
    assert result.risk_level == LEVEL_DANGEROUS, result.matched_rules
    assert result.evidence, "tin nguy hiểm phải kèm bằng chứng giải thích"
    assert result.confidence_score >= 0.5


@pytest.mark.parametrize("message", SAFE_MESSAGES)
def test_safe_messages_are_not_flagged(message):
    result = analyze(message, use_ml=False)
    assert result.risk_level == LEVEL_SAFE, (result.risk_score, result.matched_rules)
    assert result.evidence == []


def test_teacher_self_intro_with_money_request_still_dangerous():
    """Ban va bao nham o tren khong duoc lam mat canh bao khi co hoi tien."""
    result = analyze("cô my đây con làm bài tập xong thì nạp hộ cô thẻ 100k nhé", use_ml=False)
    assert result.risk_level == LEVEL_DANGEROUS, (result.risk_score, result.matched_rules)


def test_suspicious_middle_band():
    result = analyze("Mời bạn vào nhóm học tiếng Anh online, link nhóm đây nhé.", use_ml=False)
    assert result.risk_level == LEVEL_SUSPICIOUS, (result.risk_score, result.matched_rules)


@pytest.mark.parametrize(
    "message,category",
    [
        ("Thầy Hùng đây, em nạp hộ thầy thẻ 200k nhé.", CATEGORY_IMPERSONATION_TEACHER),
        ("Đọc mã OTP vừa gửi để nhận quà nhé em.", CATEGORY_OTP_PHISHING),
        ("Chúc mừng bạn trúng thưởng iPhone 15, đóng 350k phí vận chuyển để nhận.", CATEGORY_FAKE_PRIZE),
        ("Nếu không chuyển 500k tao sẽ phát tán ảnh của mày.", CATEGORY_ACCOUNT_THREAT),
    ],
)
def test_scam_category_detection(message, category):
    assert analyze(message, use_ml=False).scam_category == category


def test_evidence_phrases_come_from_original_text():
    message = "Thầy Nam thể dục đây, nạp hộ thầy 2 thẻ Viettel 100k gấp."
    result = analyze(message, use_ml=False)
    for item in result.evidence:
        if item["phrase"]:
            assert item["phrase"] in message, f"{item['phrase']!r} không có trong tin nhắn gốc"


def test_obfuscated_otp_request_is_caught():
    result = analyze("cho anh xin m4 0tp ngay", use_ml=False)
    assert result.risk_level == LEVEL_DANGEROUS


def test_output_schema_matches_specification():
    payload = analyze("Nhập mã OTP để nhận Robux miễn phí tại robux-thcs.vip", use_ml=False).to_dict()
    for key in ("risk_level", "risk_color", "confidence_score", "scam_category",
                "trigger_evidence", "student_explanation"):
        assert key in payload
    assert payload["risk_color"] == "RED"
    assert 0.0 <= payload["confidence_score"] <= 1.0


def test_latency_under_specification_limit():
    """Dac ta Muc 6.1: do tre suy luan < 1000ms."""
    result = analyze("Thầy Nam đây, nạp hộ thầy 100k gấp nhé.", use_ml=False)
    assert result.process_time_ms < 1000