"""Kiem thu phan tich ten mien - phan da sua nho kiem dinh tren du lieu SMS that."""

from __future__ import annotations

import pytest

from app.classifier import analyze
from app.config import LEVEL_DANGEROUS, LEVEL_SAFE
from app.domains import (
    brands_in,
    extract_urls,
    host_of,
    is_official,
    looks_random,
    registrable_domain,
    typo_of_brand,
)
from app.link_analyzer import analyze_links


@pytest.mark.parametrize(
    "url,expected_host",
    [
        ("https://viettel.vn/xacthucTB", "viettel.vn"),
        ("http://192.168.10.5/anh.apk", "192.168.10.5"),
        ("www.vietcombank.vn-gll.top/login", "www.vietcombank.vn-gll.top"),
    ],
)
def test_host_extraction(url, expected_host):
    assert host_of(url) == expected_host


def test_registrable_domain_handles_vietnamese_suffixes():
    assert registrable_domain("tin.vietcombank.com.vn") == "vietcombank.com.vn"
    assert registrable_domain("vietcombank.vn-gll.top") == "vn-gll.top"


@pytest.mark.parametrize(
    "host,official",
    [
        ("viettel.vn", True),
        ("chat.zalo.me", True),
        ("olm.vn", True),
        ("vietcombank.vn-gll.top", False),
        ("robux-thcs.vip", False),
    ],
)
def test_official_domain_whitelist(host, official):
    assert is_official(host) is official


def test_typo_domain_detection():
    assert typo_of_brand("vietinbamk.com") == ("vietinbamk", "vietinbank")
    assert typo_of_brand("vietinbank.vn") is None


def test_random_looking_domain():
    assert looks_random("qwrtpl.xyz") is True
    assert looks_random("hocmai.vn") is False


def test_official_links_are_not_flagged():
    """Lỗi nghiêm trọng của phiên bản đầu: `viettel.vn` bị coi là trang giả mạo."""
    for text in [
        "Truy cập https://viettel.vn/xacthucTB (app My Viettel) để xác thực thuê bao",
        "Cô gửi bài tập ở https://olm.vn nhé",
        "Vào nhóm lớp tại https://chat.zalo.me/g/abcxyz",
    ]:
        assert analyze_links(text) == [], text


@pytest.mark.parametrize(
    "text,rule_id",
    [
        ("vui long vao https://vietcombank.vn-gll.top de doi mat khau", "LINK_BRAND_IMPERSONATION"),
        ("dang nhap vietinbamk.com ngay hom nay", "LINK_BRAND_TYPO"),
        ("nhan qua tai http://bit.ly/qua-tang", "LINK_SHORTENER"),
        ("tai ve tai http://192.168.10.5/app.apk", "LINK_IP_ADDRESS"),
        ("nhan thuong tai trungthuong-2025.club", "LINK_SUSPICIOUS_TLD"),
    ],
)
def test_suspicious_links_are_flagged(text, rule_id):
    assert rule_id in {hit.rule_id for hit in analyze_links(text)}


def test_official_bank_notice_stays_calm():
    """Tin ngân hàng *thông báo* OTP không được coi là kẻ lạ *đòi* OTP."""
    text = (
        "Ma OTP xac thuc GD la 066595, hieu luc 5 phut. "
        "Tuyet doi khong cung cap ma OTP cho bat ky ai."
    )
    result = analyze(text, use_ml=False)
    assert result.risk_level != LEVEL_DANGEROUS, result.matched_rules


def test_bank_phishing_is_caught():
    text = (
        "Tai khoan cua ban dang duoc dang nhap tren thiet bi khac, "
        "neu khong phai ban vui long vao https://vietcombank.vn-gll.top de doi mat khau"
    )
    result = analyze(text, use_ml=False)
    assert result.risk_level == LEVEL_DANGEROUS


def test_carrier_promo_is_not_a_red_alert():
    text = (
        "TB MUNG QUOC KHANH! Viettel khuyen mai 20% gia tri the nap trong ngay 31/08. "
        "Chi tiet lien he 198 hoac truy cap https://vietteltelecom.vn/uudai"
    )
    assert analyze(text, use_ml=False).risk_level != LEVEL_DANGEROUS


def test_extract_urls_ignores_text_glued_to_vietnamese_word():
    """`...chúng tôizalo.me/abc` không được coi là tên miền.

    Bản JavaScript từng cắt nhầm thành `izalo.me` vì `\\w` trong JS chỉ tính ký tự
    ASCII — đã xử lý trong app/engine_export.py.
    """
    assert extract_urls("lien he voi chúng tôizalo.me/123456") == []


def test_blocklist_is_optional():
    """Không có tệp danh sách đen thì hệ thống vẫn chạy bình thường."""
    from app.domains import is_blocklisted

    assert is_blocklisted("khong-ton-tai-abcxyz.com") in (True, False)


def test_school_message_with_link_stays_safe():
    assert analyze("Cô gửi link bài tập trên https://olm.vn, các em làm trước thứ 3.", use_ml=False).risk_level == LEVEL_SAFE
