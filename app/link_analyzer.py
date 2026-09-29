"""Phan tich duong link trong tin nhan (bo sung cho bo luat regex).

Regex khong the tra loi cau hoi "ten mien nay co chinh thong khong". Module nay
so sanh tung ten mien voi danh sach trang chinh thong, phat hien ten mien nhai
thuong hieu, ten mien ngau nhien, link rut gon, dia chi IP...

Day la ket qua truc tiep tu viec kiem dinh tren du lieu SMS that: bo luat cu
canh bao nham ca `viettel.vn` va `momo.vn` chi vi co ten thuong hieu ben trong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.config import CATEGORY_PHISHING_LINK
from app.domains import (
    RISKY_TLDS,
    is_blocklisted,
    brands_in,
    extract_urls,
    host_of,
    is_official,
    looks_random,
    registrable_domain,
    tld_of,
    typo_of_brand,
)

SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "rebrand.ly", "cutt.ly", "t.ly", "is.gd",
    "s.id", "shorturl.at", "link.vn", "vt.tiktok.com", "zalo.link", "l.ink",
}

IP_HOST = "__ip__"


@dataclass
class LinkHit:
    """Mot phat hien ve duong link, dung chung dinh dang voi luat regex."""

    rule_id: str
    url: str
    reason: str
    weight: float
    hard_danger: bool = False
    standalone: bool = False
    category: str = CATEGORY_PHISHING_LINK


def _is_ip_host(host: str) -> bool:
    parts = host.split(".")
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def analyze_links(text: str) -> List[LinkHit]:
    """Cham diem rui ro cho tat ca duong link tim thay trong tin nhan."""
    hits: List[LinkHit] = []
    for url in extract_urls(text):
        host = host_of(url)
        if not host or "." not in host:
            continue

        if _is_ip_host(host):
            hits.append(
                LinkHit(
                    rule_id="LINK_IP_ADDRESS",
                    url=url,
                    reason="Đường dẫn trỏ thẳng tới địa chỉ IP — gần như chắc chắn không phải trang chính thống.",
                    weight=0.55,
                    standalone=True,
                )
            )
            continue

        if is_blocklisted(host):
            # Ten mien da bi cong dong an ninh mang to cao - khong can suy doan them.
            hits.append(
                LinkHit(
                    rule_id="LINK_BLOCKLISTED",
                    url=url,
                    reason=(
                        f"Địa chỉ `{host}` nằm trong danh sách đen các trang lừa đảo/độc hại "
                        "do cộng đồng an ninh mạng công bố."
                    ),
                    weight=0.9,
                    hard_danger=True,
                    standalone=True,
                )
            )
            continue

        if is_official(host):
            # Trang chinh thong: khong tinh diem rui ro cho ten mien nay.
            continue

        domain = registrable_domain(host)
        brands = brands_in(host)
        typo = typo_of_brand(host)
        tld = tld_of(host)

        if brands:
            # Ten mien co ten thuong hieu + duoi la (.top, .vip, .cc...) hoac co dau gach noi
            # => gan nhu chac chan gia mao. Neu duoi binh thuong (.vn/.com) thi co the la
            # trang con hop le chua co trong danh sach, nen chi canh bao muc vua.
            blatant = tld in RISKY_TLDS or "-" in host
            hits.append(
                LinkHit(
                    rule_id="LINK_BRAND_IMPERSONATION" if blatant else "LINK_BRAND_UNVERIFIED",
                    url=url,
                    reason=(
                        f"Địa chỉ `{host}` mượn tên thương hiệu \"{brands[0]}\" nhưng KHÔNG phải "
                        "trang chính thức — đây là trang giả mạo để lừa đăng nhập."
                        if blatant
                        else f"Địa chỉ `{host}` có tên thương hiệu \"{brands[0]}\" nhưng không nằm trong "
                        "danh sách trang chính thức đã biết — cần kiểm chứng trước khi bấm."
                    ),
                    weight=0.7 if blatant else 0.45,
                    hard_danger=blatant,
                    standalone=True,
                )
            )
        elif typo:
            hits.append(
                LinkHit(
                    rule_id="LINK_BRAND_TYPO",
                    url=url,
                    reason=(
                        f"Địa chỉ `{host}` viết sai một chữ so với thương hiệu thật "
                        f"\"{typo[1]}\" — chiêu đánh lừa mắt người đọc."
                    ),
                    weight=0.7,
                    hard_danger=True,
                    standalone=True,
                )
            )
        elif domain in SHORTENERS:
            hits.append(
                LinkHit(
                    rule_id="LINK_SHORTENER",
                    url=url,
                    reason="Link rút gọn che giấu địa chỉ thật của trang web.",
                    weight=0.4,
                )
            )
        elif tld in RISKY_TLDS:
            hits.append(
                LinkHit(
                    rule_id="LINK_SUSPICIOUS_TLD",
                    url=url,
                    reason=f"Tên miền lạ đuôi `.{tld}` — hiếm khi được tổ chức chính thống sử dụng.",
                    weight=0.5,
                    standalone=True,
                )
            )
        elif looks_random(host):
            hits.append(
                LinkHit(
                    rule_id="LINK_RANDOM_DOMAIN",
                    url=url,
                    reason=f"Tên miền `{domain}` trông như chuỗi ký tự ngẫu nhiên — dấu hiệu trang dùng một lần.",
                    weight=0.45,
                    standalone=True,
                )
            )
        else:
            hits.append(
                LinkHit(
                    rule_id="LINK_UNKNOWN_DOMAIN",
                    url=url,
                    reason=f"Trang `{domain}` không nằm trong danh sách trang chính thống quen thuộc.",
                    weight=0.2,
                )
            )

        lowered = url.lower()
        if lowered.endswith((".apk", ".exe")) or ".apk?" in lowered or ".exe?" in lowered:
            hits.append(
                LinkHit(
                    rule_id="LINK_FILE_DOWNLOAD",
                    url=url,
                    reason="Link tải thẳng tệp cài đặt (.apk/.exe) — thường là phần mềm theo dõi hoặc chiếm tài khoản.",
                    weight=0.6,
                    standalone=True,
                )
            )
    return hits
