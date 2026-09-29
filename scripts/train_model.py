#!/usr/bin/env python3
"""Huan luyen mo hinh TF-IDF + LogisticRegression tu mot hoac nhieu bo du lieu JSONL.

Ba che do chia tap kiem thu:
    * ``--split-mode split``    : dung san truong ``split`` trong du lieu (bo du lieu that
      da chia san train/test co kiem soat ro ri) - **trung thuc nhat**.
    * ``--split-mode template`` : tap kiem thu chi gom cac MAU CAU chua tung thay
      (danh cho du lieu mo phong sinh tu mau cau).
    * ``--split-mode random``   : chia ngau nhien - diem se dep gia tao voi du lieu mo phong.

Vi du::

    # Chi du lieu mo phong (hoc duong)
    python scripts/train_model.py

    # Ket hop du lieu mo phong + du lieu SMS that, danh gia tren tap test that
    python scripts/fetch_external_datasets.py
    python scripts/train_model.py --dataset data/dataset_thcs_scam.jsonl \
        --dataset data/external/vi_sms_phishing.jsonl --split-mode split
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ml_model  # noqa: E402
from app.config import DATASET_FULL, LEVEL_BY_LABEL, LEVEL_DANGEROUS, MODEL_PATH  # noqa: E402
from app.datasets import load_records, source_counts, split_records  # noqa: E402


def report(y_true: Sequence[int], y_pred: Sequence[int], title: str) -> None:
    from sklearn.metrics import classification_report, confusion_matrix

    present = sorted(set(y_true) | set(y_pred))
    print(f"\n--- {title} ---")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=present,
            target_names=[LEVEL_BY_LABEL[i] for i in present],
            digits=4,
            zero_division=0,
        )
    )
    print("Ma tran nham lan (hang = that, cot = du doan):")
    print(confusion_matrix(y_true, y_pred, labels=present))

    danger_total = sum(1 for t in y_true if t == 2)
    if danger_total:
        hit = sum(1 for t, p in zip(y_true, y_pred) if t == 2 and p == 2)
        risky = sum(1 for t, p in zip(y_true, y_pred) if t == 2 and p >= 1)
        print(f"Recall {LEVEL_DANGEROUS}: {hit / danger_total:.4f} | bắt được ở mức >= 🟡: {risky / danger_total:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Huan luyen mo hinh phan loai tin nhan lua dao")
    parser.add_argument("--dataset", type=Path, action="append", help="Tệp JSONL (lặp lại được)")
    parser.add_argument("--out", type=Path, default=MODEL_PATH)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--split-mode",
        choices=["split", "template", "random"],
        default="template",
        help="Cách tách tập kiểm thử (xem phần mô tả đầu tệp)",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Chỉ đo, không lưu lại mô hình"
    )
    args = parser.parse_args()

    paths = args.dataset or [DATASET_FULL]
    print(f"Nạp dữ liệu ({args.split_mode}):")
    records = load_records(paths)

    train, test = split_records(records, args.split_mode, args.test_size, args.seed)
    print(f"\nHuấn luyện: {len(train)} mẫu | Kiểm thử: {len(test)} mẫu")
    print(f"  nguồn tập huấn luyện: {source_counts(train)}")

    pipeline = ml_model.train([r["text"] for r in train], [r["label"] for r in train])
    y_true = [r["label"] for r in test]
    y_pred = [int(v) for v in pipeline.predict([ml_model.normalize_for_model(r["text"]) for r in test])]
    report(y_true, y_pred, "Kết quả mô hình ML trên tập kiểm thử")

    # Bao cao rieng cho tung nguon du lieu trong tap kiem thu.
    sources = {r["source"] for r in test}
    if len(sources) > 1:
        for source in sorted(sources):
            idx = [i for i, r in enumerate(test) if r["source"] == source]
            report([y_true[i] for i in idx], [y_pred[i] for i in idx], f"Riêng nguồn: {source}")

    if args.no_save:
        print("\n(--no-save) Không lưu mô hình.")
        return

    final_pipeline = ml_model.train([r["text"] for r in records], [r["label"] for r in records])
    print(f"\nĐã huấn luyện lại trên toàn bộ {len(records)} mẫu và lưu tại: {ml_model.save(final_pipeline, args.out)}")


if __name__ == "__main__":
    main()
