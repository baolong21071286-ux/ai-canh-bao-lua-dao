#!/usr/bin/env python3
"""Cap nhat danh sach den ten mien tu cac nguon mo ve an ninh mang.

Y tuong: khong can doan xem mot ten mien co doc hai khong neu cong dong an ninh
mang **da xac minh va cong bo** no. Day la cach ghep tri thuc cong dong vao he thong.

Nguon mac dinh: URLhaus (abuse.ch) - danh sach URL doc hai dang hoat dong, mien phi,
cap nhat lien tuc, giay phep CC0.

    python scripts/update_blocklist.py                  # tai tu URLhaus
    python scripts/update_blocklist.py --from-file x.txt  # gop them tep rieng
    python scripts/update_blocklist.py --show           # xem thong tin danh sach hien co
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path
from typing import Iterable, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domains import BLOCKLIST_PATH, host_of, registrable_domain  # noqa: E402

SOURCES = {
    "urlhaus": {
        "url": "https://urlhaus.abuse.ch/downloads/text_online/",
        "license": "CC0 (abuse.ch)",
        "note": "URL độc hại đang hoạt động, cập nhật liên tục.",
    },
}

# Khong bao gio dua cac ten mien dich vu pho bien vao danh sach den, du chung
# co the bi ke xau loi dung de chua noi dung.
NEVER_BLOCK = {
    "github.com", "githubusercontent.com", "google.com", "drive.google.com",
    "dropbox.com", "facebook.com", "zalo.me", "discord.com", "cdn.discordapp.com",
    "blogspot.com", "wordpress.com", "weebly.com", "firebaseapp.com", "web.app",
    "amazonaws.com", "cloudfront.net", "azurewebsites.net", "pages.dev", "workers.dev",
}


def domains_from_lines(lines: Iterable[str]) -> Set[str]:
    """Lay ten mien dang ky duoc tu danh sach URL/ten mien."""
    domains: Set[str] = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        host = host_of(line)
        if not host or "." not in host:
            continue
        if re.fullmatch(r"[\d.]+", host):  # bo qua dia chi IP (da co luat rieng)
            continue
        domain = registrable_domain(host)
        if domain and domain not in NEVER_BLOCK:
            domains.add(domain)
    return domains


def fetch(url: str) -> Set[str]:
    print(f"  tải {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "thcs-scam-detector/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        text = response.read().decode("utf-8", errors="ignore")
    return domains_from_lines(text.splitlines())


def main() -> None:
    parser = argparse.ArgumentParser(description="Cap nhat danh sach den ten mien")
    parser.add_argument("--source", choices=sorted(SOURCES), default="urlhaus")
    parser.add_argument("--from-file", type=Path, help="Gộp thêm danh sách từ tệp có sẵn")
    parser.add_argument("--out", type=Path, default=BLOCKLIST_PATH)
    parser.add_argument("--show", action="store_true", help="Chỉ xem thông tin danh sách hiện có")
    args = parser.parse_args()

    if args.show:
        if args.out.exists():
            lines = [l for l in args.out.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
            print(f"{args.out}: {len(lines)} tên miền")
            print("Ví dụ:", ", ".join(lines[:5]))
        else:
            print(f"Chưa có {args.out}. Chạy: python scripts/update_blocklist.py")
        return

    domains: Set[str] = set()
    source = SOURCES[args.source]
    print(f"Nguồn: {args.source} ({source['license']}) — {source['note']}")
    domains |= fetch(source["url"])
    if args.from_file:
        domains |= domains_from_lines(args.from_file.read_text(encoding="utf-8").splitlines())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# Danh sách đen tên miền dùng cho app/link_analyzer.py",
        f"# Nguồn: {source['url']} ({source['license']})",
        "# Tệp này được tải về tự động — không commit vào kho mã nguồn.",
        f"# Số tên miền: {len(domains)}",
    ]
    args.out.write_text("\n".join(header + sorted(domains)) + "\n", encoding="utf-8")
    print(f"Đã ghi {len(domains)} tên miền vào {args.out}")


if __name__ == "__main__":
    main()
