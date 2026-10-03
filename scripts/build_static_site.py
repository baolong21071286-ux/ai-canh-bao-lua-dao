#!/usr/bin/env python3
"""Dung ban demo TINH (chay tren GitHub Pages, khong can may chu).

Toan bo luat/nguong/noi dung giao duc duoc xuat tu ma nguon Python ra
`engine-data.json` (xem app/engine_export.py), roi ghep voi `frontend/engine.js`
- ban JavaScript cua Module 1-3. Chi co MOT nguon du lieu duy nhat: sua luat
trong Python roi chay lai script nay la ban web tinh cap nhat theo.

Cac lop mo hinh (neu da huan luyen) cung duoc dong goi kem:
    * models/scam_clf.joblib  -> site/tfidf-model.json   (TF-IDF + LogisticRegression)
    * models/phobert_scam/    -> site/phobert/           (PhoBERT ONNX, trong so int8; can torch + onnx)

    python scripts/build_static_site.py          # xuat ra thu muc site/
    python scripts/build_static_site.py --no-phobert   # bo qua PhoBERT (dung nhanh)
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
    parser.add_argument("--no-phobert", action="store_true", help="Không đóng gói PhoBERT")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    data = build_engine_data()
    (args.out / "engine-data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    for name in ("index.html", "engine.js", "models.js"):
        shutil.copy2(FRONTEND_DIR / name, args.out / name)
    # GitHub Pages bo qua tep bat dau bang dau gach duoi neu thieu .nojekyll
    (args.out / ".nojekyll").write_text("", encoding="utf-8")

    from app.model_export import export_phobert, write_tfidf

    tfidf_path = write_tfidf(args.out / "tfidf-model.json")
    if tfidf_path is None:
        (args.out / "tfidf-model.json").unlink(missing_ok=True)
    phobert_dir = args.out / "phobert"
    if phobert_dir.exists():
        shutil.rmtree(phobert_dir)
    manifest = None
    if not args.no_phobert:
        try:
            manifest = export_phobert(phobert_dir)
        except ImportError as exc:
            print(f"  (!) Bỏ qua PhoBERT: thiếu thư viện ({exc.name}). Cài torch, transformers, onnx, onnxruntime.")

    size = (args.out / "engine-data.json").stat().st_size / 1024
    print(f"Đã dựng bản tĩnh tại: {args.out}")
    print(
        f"  engine-data.json: {size:.1f} KB "
        f"({len(data['rules'])} luật, {len(data['combos'])} luật kết hợp, "
        f"{len(data['education'])} kịch bản giáo dục)"
    )
    if tfidf_path:
        print(f"  tfidf-model.json: {tfidf_path.stat().st_size / 1048576:.1f} MB")
    else:
        print("  TF-IDF: chưa huấn luyện (python scripts/train_model.py) - bản web bỏ qua lớp này")
    if manifest:
        print(f"  phobert/: {manifest['totalBytes'] / 1048576:.0f} MB, {len(manifest['parts'])} mảnh")
    elif not args.no_phobert:
        print("  PhoBERT: chưa huấn luyện (python scripts/train_transformer.py) - bản web bỏ qua lớp này")
    print("  Xem thử: python -m http.server -d site 8080")


if __name__ == "__main__":
    main()