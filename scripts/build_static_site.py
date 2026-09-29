#!/usr/bin/env python3
"""Dung ban demo TINH (chay tren GitHub Pages, khong can may chu).

Toan bo luat/nguong/noi dung giao duc duoc xuat tu ma nguon Python ra
`engine-data.json` (xem app/engine_export.py), roi ghep voi `frontend/engine.js`
- ban JavaScript cua Module 1-3. Chi co MOT nguon du lieu duy nhat: sua luat
trong Python roi chay lai script nay la ban web tinh cap nhat theo.

    python scripts/build_static_site.py          # xuat ra thu muc site/
    python -m http.server -d site 8080           # xem thu
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR, FRONTEND_DIR  # noqa: E402
from app.engine_export import build_engine_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Dung ban demo tinh cho GitHub Pages")
    parser.add_argument("--out", type=Path, default=BASE_DIR / "site")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    data = build_engine_data()
    (args.out / "engine-data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    for name in ("index.html", "engine.js"):
        shutil.copy2(FRONTEND_DIR / name, args.out / name)
    # GitHub Pages bo qua tep bat dau bang dau gach duoi neu thieu .nojekyll
    (args.out / ".nojekyll").write_text("", encoding="utf-8")

    size = (args.out / "engine-data.json").stat().st_size / 1024
    print(f"Đã dựng bản tĩnh tại: {args.out}")
    print(
        f"  engine-data.json: {size:.1f} KB "
        f"({len(data['rules'])} luật, {len(data['combos'])} luật kết hợp, "
        f"{len(data['education'])} kịch bản giáo dục)"
    )
    print("  Xem thử: python -m http.server -d site 8080")


if __name__ == "__main__":
    main()
