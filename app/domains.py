"""Danh sach ten mien chinh thong va cong cu phan tich ten mien.

Bai hoc rut ra tu du lieu SMS that: bo luat cu coi *moi* ten mien co chua ten
thuong hieu la gia mao, nen bao dong nham ca `viettel.vn` lan `momo.vn`.
Cach lam dung la: **so sanh voi danh sach ten mien chinh thong**, chi canh bao khi
ten thuong hieu xuat hien tren mot ten mien KHONG chinh thong (vd `vietcombank.vn-gll.top`).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

#: Danh sach den ten mien (tuy chon). Tai ve bang scripts/update_blocklist.py.
#: Day la cach ghep them "tri thuc cong dong" (URLhaus, Chong Lua Dao...) vao he thong:
#: mot ten mien da bi cong dong to cao thi khong can doan nua.
BLOCKLIST_PATH = Path(
    os.getenv("SCAM_BLOCKLIST_PATH", Path(__file__).resolve().parent.parent / "data" / "blocklist_domains.txt")
)
_blocklist: Optional[Set[str]] = None

# Hau to ten mien cap 2 pho bien (de tach dung "ten mien dang ky duoc").
MULTI_LABEL_SUFFIXES = {
    "com.vn", "net.vn", "org.vn", "edu.vn", "gov.vn", "biz.vn", "info.vn",
    "co.uk", "com.au", "co.jp", "com.sg",
}

#: Ten mien chinh thong hay gap trong tin nhan cua hoc sinh va gia dinh Viet Nam.
OFFICIAL_DOMAINS: Set[str] = {
    # Vien thong
    "viettel.vn", "viettelstore.vn", "vinaphone.com.vn", "vnpt.com.vn", "mobifone.vn",
    "my.viettel.com.vn", "vietnamobile.com.vn", "vietteltelecom.vn", "viettelmoney.vn",
    "viettelmoney.go.link", "viettelpost.com.vn", "vnptmoney.vn", "km.vnptmoney.vn",
    "dvs.vnpt.vn", "vnpt.vn", "mobifonemoney.vn",
    # Ngan hang / vi dien tu
    "vietcombank.com.vn", "bidv.com.vn", "vietinbank.vn", "techcombank.com.vn",
    "acb.com.vn", "mbbank.com.vn", "tpb.vn", "vpbank.com.vn", "agribank.com.vn",
    "sacombank.com.vn", "vib.com.vn", "hdbank.com.vn", "momo.vn", "zalopay.vn",
    "vnpay.vn", "napas.com.vn",
    # Mang xa hoi / dich vu
    "facebook.com", "messenger.com", "zalo.me", "chat.zalo.me", "google.com",
    "youtube.com", "gmail.com", "tiktok.com", "instagram.com", "discord.com",
    "discord.gg", "apple.com", "icloud.com", "microsoft.com",
    # Game
    "roblox.com", "garena.vn", "lienquan.garena.vn", "ff.garena.com", "steampowered.com",
    # Hoc tap / co quan nha nuoc
    "moet.gov.vn", "hocmai.vn", "olm.vn", "quizizz.com", "vnedu.vn", "k12online.vn",
    "dichvucong.gov.vn", "baohiemxahoi.gov.vn", "gdt.gov.vn",
    # Thuong mai dien tu / van chuyen
    "shopee.vn", "lazada.vn", "tiki.vn", "ghn.vn", "ghtk.vn", "vnpost.vn", "sendo.vn",
}

#: Ten thuong hieu hay bi gia mao trong tin nhan lua dao.
BRAND_TOKENS: Set[str] = {
    "viettel", "vinaphone", "vnpt", "mobifone", "vietcombank", "vietinbank", "bidv",
    "techcombank", "sacombank", "agribank", "mbbank", "acb", "tpbank", "vpbank",
    "momo", "zalopay", "vnpay", "facebook", "zalo", "google", "gmail", "tiktok",
    "shopee", "lazada", "tiki", "roblox", "robux", "garena", "lienquan", "freefire",
    "discord", "apple", "icloud", "netflix", "spotify", "vieon", "vnedu", "dichvucong",
}

#: Duoi ten mien hiem khi duoc dung boi to chuc chinh thong tai Viet Nam.
RISKY_TLDS = {
    "vip", "top", "xyz", "club", "icu", "cf", "tk", "ga", "gq", "ml", "buzz", "win",
    "bar", "rest", "cc", "me", "su", "pw", "click", "link", "life", "fun", "quest",
    "monster", "sbs", "cyou", "makeup", "autos", "ru",
}

URL_IN_TEXT_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"'()\[\],]+"
    r"|(?<![@\w.])[a-z0-9][a-z0-9\-]{1,40}(?:\.[a-z0-9\-]{1,30})+\.[a-z]{2,6}(?:/[^\s<>\"'()\[\],]*)?"
    r"|(?<![@\w.])[a-z0-9][a-z0-9\-]{1,40}\.(?:com|vn|net|org|info|biz|vip|top|xyz|club|icu|cc|me|tk|ml|ga|cf|gq|buzz|win|shop|online|site|store|app|link|live|fun)"
    r"(?:/[^\s<>\"'()\[\],]*)?",
    re.IGNORECASE,
)


def extract_urls(text: str) -> List[str]:
    """Lay danh sach URL/ten mien xuat hien trong tin nhan."""
    seen, out = set(), []
    for match in URL_IN_TEXT_RE.finditer(text):
        url = match.group(0).rstrip(".,;:!?)")
        key = url.lower()
        if key not in seen:
            seen.add(key)
            out.append(url)
    return out


def host_of(url: str) -> str:
    """Lay phan ten may chu (host) tu mot URL/ten mien."""
    host = re.sub(r"^[a-z]+://", "", url.strip(), flags=re.IGNORECASE)
    host = host.split("/")[0].split("?")[0].split("#")[0]
    host = host.split("@")[-1].split(":")[0]
    return host.lower().strip(".")


def registrable_domain(host: str) -> str:
    """Lay ten mien dang ky duoc: `vn-gll.top` tu `vietcombank.vn-gll.top`."""
    labels = [part for part in host.split(".") if part]
    if len(labels) <= 2:
        return ".".join(labels)
    last_two = ".".join(labels[-2:])
    if last_two in MULTI_LABEL_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return last_two


def tld_of(host: str) -> str:
    return host.rsplit(".", 1)[-1] if "." in host else ""


def is_official(host: str) -> bool:
    """Ten mien co nam trong danh sach chinh thong khong (ke ca ten mien con)."""
    host = host.lower().strip(".")
    if not host:
        return False
    for official in OFFICIAL_DOMAINS:
        if host == official or host.endswith("." + official):
            return True
    return registrable_domain(host) in OFFICIAL_DOMAINS


def brands_in(host: str) -> List[str]:
    """Cac ten thuong hieu xuat hien trong ten may chu."""
    flat = re.sub(r"[^a-z0-9]", "", host.lower())
    return sorted({brand for brand in BRAND_TOKENS if brand in flat})


def looks_random(host: str) -> bool:
    """Ten mien trong nhu chuoi ky tu ngau nhien (dau hieu ten mien dung mot lan).

    Vi du that trong du lieu: ``ebmld.kejda.me``, ``DrnJmi.LoZuF.me``.
    """
    label = registrable_domain(host).split(".")[0]
    if len(label) < 5 or not label.isalpha():
        return False
    vowels = sum(1 for ch in label if ch in "aeiouy")
    ratio = vowels / len(label)
    longest_consonant_run = max(
        (len(run) for run in re.findall(r"[^aeiouy]+", label)), default=0
    )
    return ratio < 0.3 or longest_consonant_run >= 4


def typo_of_brand(host: str) -> Optional[Tuple[str, str]]:
    """Phat hien ten mien go nhai thuong hieu (vietinbamk, tech-com-priority...).

    Tra ve ``(nhan_mien, thuong_hieu_bi_nhai)`` neu nghi ngo.
    """
    label = re.sub(r"[^a-z0-9]", "", registrable_domain(host).split(".")[0].lower())
    if len(label) < 5:
        return None
    for brand in BRAND_TOKENS:
        if len(brand) < 5 or brand in label:
            continue
        if _edit_distance_at_most(label, brand, 2) and abs(len(label) - len(brand)) <= 2:
            return label, brand
    return None


def _edit_distance_at_most(a: str, b: str, limit: int) -> bool:
    """Kiem tra khoang cach Levenshtein giua hai chuoi co <= `limit` hay khong."""
    if abs(len(a) - len(b)) > limit:
        return False
    previous = list(range(len(b) + 1))
    for i, ch_a in enumerate(a, start=1):
        current = [i]
        for j, ch_b in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ch_a != ch_b),
                )
            )
        if min(current) > limit:
            return False
        previous = current
    return previous[-1] <= limit


def load_blocklist(path: Path = None, force: bool = False) -> Set[str]:
    """Nap danh sach den ten mien (neu co). Khong co tep thi tra ve tap rong."""
    global _blocklist
    if _blocklist is not None and not force:
        return _blocklist
    path = Path(path or BLOCKLIST_PATH)
    entries: Set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip().lower()
            if line and not line.startswith("#"):
                entries.add(line.lstrip("."))
    _blocklist = entries
    return _blocklist


def is_blocklisted(host: str) -> bool:
    """Ten mien (hoac ten mien cha cua no) co nam trong danh sach den khong."""
    blocklist = load_blocklist()
    if not blocklist:
        return False
    host = host.lower().strip(".")
    if host in blocklist or registrable_domain(host) in blocklist:
        return True
    parts = host.split(".")
    return any(".".join(parts[i:]) in blocklist for i in range(1, len(parts) - 1))
