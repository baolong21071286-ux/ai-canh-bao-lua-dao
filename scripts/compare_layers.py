#!/usr/bin/env python3
"""So sanh dong gop cua TUNG LOP trong he thong lai.

Chay lan luot 4 cau hinh tren cung mot tap du lieu de thay ro moi lop them duoc gi:

    1. Chi bo luat
    2. Bo luat + TF-IDF
    3. Bo luat + PhoBERT
    4. Ca ba lop

Quan trong: mo hinh phai duoc huan luyen tren TAP TRAIN va danh gia tren TAP TEST
chua tung thay, neu khong con so se lac quan gia tao. Vi du::

    # 1) Huan luyen tren tap train
    python scripts/train_model.py --dataset ... --split-mode split
    python scripts/train_transformer.py --dataset ... --split-mode split

    # 2) So sanh tren tap test
    SCAM_MODEL_PATH=models/tfidf_trainsplit.joblib \\
    python scripts/compare_layers.py --dataset data/external/test_split.jsonl --binary
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ml_model, transformer_model  # noqa: E402
from app.config import DATASET_FULL, LABEL_BY_LEVEL  # noqa: E402
from app.datasets import load_records  # noqa: E402


def _metrics_binary(y_true: Sequence[int], y_pred: Sequence[int], alarm_from: int) -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t >= 1 and p >= alarm_from)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t >= 1 and p < alarm_from)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p >= alarm_from)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p < alarm_from)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "accuracy": (tp + tn) / max(1, len(y_true)),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "fp": fp,
        "fn": fn,
    }


def _metrics_three_level(y_true: Sequence[int], y_pred: Sequence[int]) -> dict:
    danger = sum(1 for t in y_true if t == 2) or 1
    return {
        "accuracy": sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(1, len(y_true)),
        "recall": sum(1 for t, p in zip(y_true, y_pred) if t == 2 and p == 2) / danger,
        "precision": 0.0,
        "f1": 0.0,
        "fp": sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 2),
        "fn": sum(1 for t, p in zip(y_true, y_pred) if t == 2 and p == 0),
    }


def run_config(records, use_tfidf: bool, use_transformer: bool) -> Tuple[List[int], List[float]]:
    """Chay he thong voi mot to hop lop cu the bang cach tat/bat tam thoi."""
    from app import classifier

    original_ml = classifier.ml_model.predict_proba
    original_tr = classifier.transformer_model.predict_proba
    if not use_tfidf:
        classifier.ml_model.predict_proba = lambda text: None
    if not use_transformer:
        classifier.transformer_model.predict_proba = lambda text: None
    try:
        preds, latencies = [], []
        for record in records:
            started = time.perf_counter()
            result = classifier.analyze(record["text"], use_ml=True)
            latencies.append((time.perf_counter() - started) * 1000)
            preds.append(LABEL_BY_LEVEL[result.risk_level])
        return preds, latencies
    finally:
        classifier.ml_model.predict_proba = original_ml
        classifier.transformer_model.predict_proba = original_tr


def main() -> None:
    parser = argparse.ArgumentParser(description="So sanh dong gop cua tung lop mo hinh")
    parser.add_argument("--dataset", type=Path, action="append")
    parser.add_argument("--binary", action="store_true", help="Dữ liệu chỉ có nhãn hợp lệ/lừa đảo")
    parser.add_argument(
        "--alarm-from",
        type=int,
        choices=[1, 2],
        default=1,
        help="1 = coi 🟡 và 🔴 đều là cảnh báo (mặc định); 2 = chỉ tính 🔴",
    )
    args = parser.parse_args()

    print("Nạp dữ liệu:")
    records = load_records(args.dataset or [DATASET_FULL])
    y_true = [r["label"] for r in records]

    tfidf_ready = ml_model.is_available()
    transformer_ready = transformer_model.is_available()
    print(f"\nLớp sẵn có — TF-IDF: {tfidf_ready} | PhoBERT: {transformer_ready}")
    if transformer_ready:
        print(f"  (PhoBERT: {transformer_model.TRANSFORMER_DIR})")

    configs = [("Chỉ bộ luật", False, False)]
    if tfidf_ready:
        configs.append(("Bộ luật + TF-IDF", True, False))
    if transformer_ready:
        configs.append(("Bộ luật + PhoBERT", False, True))
    if tfidf_ready and transformer_ready:
        configs.append(("Cả ba lớp", True, True))

    header = f"{'Cấu hình':22s} {'Accuracy':>9s} {'Recall':>8s} {'F1':>8s} {'Báo nhầm':>9s} {'Bỏ sót':>7s} {'ms/tin':>7s}"
    print("\n" + header)
    print("-" * len(header))
    for name, use_tfidf, use_transformer in configs:
        preds, latencies = run_config(records, use_tfidf, use_transformer)
        m = _metrics_binary(y_true, preds, args.alarm_from) if args.binary else _metrics_three_level(y_true, preds)
        print(
            f"{name:22s} {m['accuracy']:9.4f} {m['recall']:8.4f} {m['f1']:8.4f} "
            f"{m['fp']:9d} {m['fn']:7d} {statistics.mean(latencies):7.1f}"
        )
    print("\nBáo nhầm = tin hợp lệ bị cảnh báo · Bỏ sót = tin lừa đảo bị coi là an toàn")


if __name__ == "__main__":
    main()
