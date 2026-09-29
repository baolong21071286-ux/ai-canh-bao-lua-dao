#!/usr/bin/env python3
"""Tinh chinh (fine-tune) mo hinh Transformer tieng Viet cho bai toan phan loai tin nhan.

Mac dinh dung **PhoBERT-base-v2** (VinAI Research, giay phep MIT) - mo hinh ngon ngu
tieng Viet ma nguon mo pho bien nhat. Co the doi sang mo hinh khac bang `--model-name`
(vi du `xlm-roberta-base`, `distilbert-base-multilingual-cased`).

Chay duoc tren CPU (cham hon nhung khong can GPU)::

    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install transformers

    python scripts/train_transformer.py \
        --dataset data/dataset_thcs_scam.jsonl \
        --dataset data/external/vi_sms_phishing.jsonl \
        --split-mode split --epochs 3
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATASET_FULL, LEVEL_BY_LABEL  # noqa: E402
from app.datasets import load_records, source_counts, split_records  # noqa: E402
from app.transformer_model import DEFAULT_BASE_MODEL, MAX_LENGTH, TRANSFORMER_DIR  # noqa: E402


def encode(tokenizer, texts: Sequence[str]):
    return tokenizer(
        list(texts), truncation=True, max_length=MAX_LENGTH, padding=True, return_tensors="pt"
    )


def evaluate(model, tokenizer, records: Sequence[dict], batch_size: int, title: str) -> List[int]:
    import torch
    from sklearn.metrics import classification_report, confusion_matrix

    model.eval()
    preds: List[int] = []
    with torch.no_grad():
        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]
            encoded = encode(tokenizer, [r["text"] for r in batch])
            logits = model(**encoded).logits
            preds.extend(int(i) for i in logits.argmax(dim=-1).tolist())

    y_true = [r["label"] for r in records]
    label_map = sorted({*y_true, *preds})
    print(f"\n--- {title} ---")
    print(
        classification_report(
            y_true,
            preds,
            labels=label_map,
            target_names=[LEVEL_BY_LABEL[i] for i in label_map],
            digits=4,
            zero_division=0,
        )
    )
    print(confusion_matrix(y_true, preds, labels=label_map))
    return preds


def main() -> None:
    parser = argparse.ArgumentParser(description="Tinh chinh PhoBERT cho phan loai tin nhan lua dao")
    parser.add_argument("--dataset", type=Path, action="append")
    parser.add_argument("--model-name", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--out", type=Path, default=TRANSFORMER_DIR)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--split-mode", choices=["split", "template", "random"], default="split")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--max-train", type=int, default=0, help="Giới hạn số mẫu huấn luyện (0 = tất cả)")
    args = parser.parse_args()

    try:
        import torch
        from torch.optim import AdamW
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup
    except ImportError as exc:
        raise SystemExit(
            "Thiếu thư viện. Cài đặt:\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install transformers"
        ) from exc

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    print(f"Nạp dữ liệu ({args.split_mode}):")
    records = load_records(args.dataset or [DATASET_FULL])
    train, test = split_records(records, args.split_mode, args.test_size, args.seed)
    if args.max_train:
        random.shuffle(train)
        train = train[: args.max_train]
    labels = sorted({r["label"] for r in records})
    print(f"\nHuấn luyện: {len(train)} | Kiểm thử: {len(test)} | nhãn: {labels}")
    print(f"  nguồn tập huấn luyện: {source_counts(train)}")

    print(f"\nTải mô hình nền: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, num_labels=len(labels)
    )
    torch.set_num_threads(max(1, torch.get_num_threads()))

    label_to_index = {label: index for index, label in enumerate(labels)}
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps_per_epoch = math.ceil(len(train) / args.batch_size)
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * total_steps), total_steps)

    # Trong so lop: uu tien Recall cho nhan nguy hiem (Muc 6.1 cua dac ta).
    counts = {label: sum(1 for r in train if r["label"] == label) for label in labels}
    weights = torch.tensor(
        [len(train) / (len(labels) * max(1, counts[label])) for label in labels], dtype=torch.float
    )
    if 2 in label_to_index:
        weights[label_to_index[2]] *= 1.3
    print(f"  phân bố nhãn: {counts} | trọng số lớp: {[round(float(w), 3) for w in weights]}")
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)

    started = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        random.shuffle(train)
        running = 0.0
        for step, start in enumerate(range(0, len(train), args.batch_size), start=1):
            batch = train[start : start + args.batch_size]
            encoded = encode(tokenizer, [r["text"] for r in batch])
            targets = torch.tensor([label_to_index[r["label"]] for r in batch])
            outputs = model(**encoded)
            loss = loss_fn(outputs.logits, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            running += loss.item()
            if step % 20 == 0 or step == steps_per_epoch:
                elapsed = time.time() - started
                print(
                    f"  epoch {epoch}/{args.epochs} · bước {step}/{steps_per_epoch} · "
                    f"loss {running / step:.4f} · {elapsed / 60:.1f} phút",
                    flush=True,
                )
        # Doi chieu chi so lop ve nhan goc khi danh gia.
        index_to_label = {index: label for label, index in label_to_index.items()}
        holdout = [dict(r, label=r["label"]) for r in test]
        preds = evaluate(model, tokenizer, holdout, args.batch_size, f"Sau epoch {epoch}")
        del preds, index_to_label

    args.out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.out))
    tokenizer.save_pretrained(str(args.out))
    (args.out / "label_map.json").write_text(
        json.dumps({"labels": labels, "base_model": args.model_name}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nĐã lưu mô hình tại: {args.out}  (tổng {(time.time() - started) / 60:.1f} phút)")


if __name__ == "__main__":
    main()
