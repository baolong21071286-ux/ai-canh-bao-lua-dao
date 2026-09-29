#!/usr/bin/env python3
"""Danh gia he thong theo cac chi so o Muc 6.1 cua dac ta.

Do 3 cau hinh de thay ro dong gop cua tung thanh phan:
    1. Chi bo luat (rule-based) - luon giai thich duoc.
    2. Chi mo hinh ML.
    3. Hybrid (mac dinh cua he thong).

Chi so bao cao: Accuracy tong the, Recall tren nhan DANGEROUS, do tre trung binh/p95.

Cach dung::

    python scripts/evaluate.py --dataset data/dataset_thcs_scam.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ml_model  # noqa: E402
from app.classifier import analyze  # noqa: E402
from app.config import DATASET_FULL, LABEL_BY_LEVEL, LEVEL_BY_LABEL  # noqa: E402

DANGEROUS_LABEL = 2


def load_dataset(path: Path) -> Tuple[List[str], List[int]]:
    texts, labels = [], []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                record = json.loads(line)
                texts.append(record["text"])
                labels.append(int(record["label"]))
    return texts, labels


def _metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> dict:
    n = len(y_true)
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / n
    danger_total = sum(1 for t in y_true if t == DANGEROUS_LABEL)
    danger_hit = sum(1 for t, p in zip(y_true, y_pred) if t == DANGEROUS_LABEL and p == DANGEROUS_LABEL)
    # "Bo sot nguy hiem": tin lua dao bi xep vao nhom An toan - loi nghiem trong nhat.
    missed_to_safe = sum(1 for t, p in zip(y_true, y_pred) if t == DANGEROUS_LABEL and p == 0)
    recall_danger = danger_hit / danger_total if danger_total else 0.0
    caught_as_risky = sum(
        1 for t, p in zip(y_true, y_pred) if t == DANGEROUS_LABEL and p >= 1
    ) / (danger_total or 1)
    false_alarm = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == DANGEROUS_LABEL)
    safe_total = sum(1 for t in y_true if t == 0) or 1
    return {
        "accuracy": accuracy,
        "recall_dangerous": recall_danger,
        "dangerous_caught_as_risky": caught_as_risky,
        "dangerous_missed_as_safe": missed_to_safe,
        "false_alarm_rate_on_safe": false_alarm / safe_total,
    }


def _confusion(y_true: Sequence[int], y_pred: Sequence[int]) -> List[List[int]]:
    matrix = [[0, 0, 0] for _ in range(3)]
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1
    return matrix


def _binary_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> dict:
    """Quy ve nhi phan: 'co canh bao' (🟡 hoac 🔴) vs 'an toan' (🟢)."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t >= 1 and p >= 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t >= 1 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p >= 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": (tp + tn) / max(1, len(y_true)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fp / max(1, fp + tn),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def _print_binary_block(title: str, y_true: Sequence[int], y_pred: Sequence[int], latencies: Sequence[float]) -> None:
    m = _binary_metrics(y_true, y_pred)
    print(f"\n=== {title} (che do nhi phan) ===")
    print(f"Accuracy               : {m['accuracy']:.4f}")
    print(f"Precision (canh bao)   : {m['precision']:.4f}")
    print(f"Recall (bat lua dao)   : {m['recall']:.4f}")
    print(f"F1                     : {m['f1']:.4f}")
    print(f"Ti le bao dong nham    : {m['false_positive_rate']:.4f}  ({m['fp']}/{m['fp'] + m['tn']} tin hop le)")
    print(f"Bo sot                 : {m['fn']} tin lua dao bi coi la an toan")
    if latencies:
        print(
            f"Do tre: trung binh {statistics.mean(latencies):.2f} ms | "
            f"p95 {sorted(latencies)[int(0.95 * len(latencies)) - 1]:.2f} ms"
        )


def _print_block(title: str, y_true: Sequence[int], y_pred: Sequence[int], latencies: Sequence[float]) -> None:
    metrics = _metrics(y_true, y_pred)
    print(f"\n=== {title} ===")
    print(f"Accuracy               : {metrics['accuracy']:.4f}")
    print(f"Recall (DANGEROUS)     : {metrics['recall_dangerous']:.4f}")
    print(f"Bat duoc o muc >= vang : {metrics['dangerous_caught_as_risky']:.4f}")
    print(f"Bo sot (nguy hiem->an toan): {metrics['dangerous_missed_as_safe']}")
    print(f"Bao dong nham tren tin an toan: {metrics['false_alarm_rate_on_safe']:.4f}")
    if latencies:
        print(
            f"Do tre: trung binh {statistics.mean(latencies):.2f} ms | "
            f"p95 {sorted(latencies)[int(0.95 * len(latencies)) - 1]:.2f} ms | "
            f"max {max(latencies):.2f} ms"
        )
    print("Ma tran nham lan (hang = that, cot = du doan) [SAFE, SUSPICIOUS, DANGEROUS]:")
    for row_label, row in zip(["SAFE      ", "SUSPICIOUS", "DANGEROUS "], _confusion(y_true, y_pred)):
        print(f"  {row_label} {row}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Danh gia he thong canh bao tin nhan lua dao")
    parser.add_argument("--dataset", type=Path, default=DATASET_FULL)
    parser.add_argument("--limit", type=int, default=0, help="Chi danh gia N mau dau tien (0 = tat ca)")
    parser.add_argument(
        "--binary",
        action="store_true",
        help=(
            "Che do nhi phan cho cac bo du lieu chi co nhan 'hop le / lua dao' "
            "(vd bo du lieu that tai bang scripts/fetch_external_datasets.py): "
            "coi ca 🟡 va 🔴 deu la 'co canh bao'"
        ),
    )
    args = parser.parse_args()

    texts, labels = load_dataset(args.dataset)
    if args.limit:
        texts, labels = texts[: args.limit], labels[: args.limit]
    print(f"Đã nạp {len(texts)} mẫu từ {args.dataset}")
    print(
        "LƯU Ý: nếu mô hình ML được huấn luyện trên chính tập dữ liệu này thì các con số\n"
        "       ở mục ML/Hybrid là điểm 'trong mẫu' (in-sample) và sẽ đẹp hơn thực tế.\n"
        "       Con số trung thực nằm ở scripts/train_model.py --split-mode template."
    )

    def run(use_ml: bool):
        preds, latencies = [], []
        for text in texts:
            started = time.perf_counter()
            result = analyze(text, use_ml=use_ml)
            latencies.append((time.perf_counter() - started) * 1000)
            preds.append(LABEL_BY_LEVEL[result.risk_level])
        return preds, latencies

    if args.binary:
        rule_pred, rule_latency = run(use_ml=False)
        _print_binary_block("CHI BO LUAT", labels, rule_pred, rule_latency)
        if ml_model.is_available():
            hybrid_pred, hybrid_latency = run(use_ml=True)
            _print_binary_block("HYBRID (bo luat + ML)", labels, hybrid_pred, hybrid_latency)
        else:
            print("\n(!) Chua co mo hinh ML - bo qua phan danh gia Hybrid.")
        return

    # --- 1. Chi bo luat ---
    rule_pred, rule_latency = run(use_ml=False)
    _print_block("CHI BO LUAT (rule-based, 100% giai thich duoc)", labels, rule_pred, rule_latency)

    # --- 2. Chi mo hinh ML ---
    if ml_model.is_available():
        model = ml_model.load()
        ml_pred, ml_latency = [], []
        for text in texts:
            started = time.perf_counter()
            pred = int(model.predict([ml_model.normalize_for_model(text)])[0])
            ml_latency.append((time.perf_counter() - started) * 1000)
            ml_pred.append(pred)
        _print_block("CHI MO HINH ML (TF-IDF + LogisticRegression)", labels, ml_pred, ml_latency)

        # --- 3. Hybrid ---
        hybrid_pred, hybrid_latency = run(use_ml=True)
        _print_block("HYBRID (mac dinh cua he thong)", labels, hybrid_pred, hybrid_latency)
    else:
        print("\n(!) Chua co mo hinh ML - bo qua phan danh gia ML/Hybrid.")
        print("    Chay: python scripts/train_model.py")


if __name__ == "__main__":
    main()
