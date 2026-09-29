"""Nap va chia bo du lieu JSONL - dung chung cho cac script huan luyen/danh gia."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SPLIT_MODES = ("split", "template", "random")


def load_records(paths: Sequence[Path]) -> List[dict]:
    """Nap nhieu tep JSONL, gan them truong `source` theo ten tep."""
    records: List[dict] = []
    for path in paths:
        path = Path(path)
        if not path.exists():
            raise SystemExit(
                f"Không tìm thấy {path}. Sinh dữ liệu bằng data/generate_sample_dataset.py "
                "hoặc tải dữ liệu ngoài bằng scripts/fetch_external_datasets.py"
            )
        count = 0
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    record = json.loads(line)
                    record.setdefault("source", path.stem)
                    records.append(record)
                    count += 1
        print(f"  {path}: {count} mẫu")
    return records


def split_records(
    records: List[dict], mode: str = "template", test_size: float = 0.2, seed: int = 42
) -> Tuple[List[dict], List[dict]]:
    """Chia train/test.

    * ``split``    - dung truong `split` co san (bo du lieu that da chia san).
    * ``template`` - tap kiem thu chi gom cac mau cau chua tung thay.
    * ``random``   - chia ngau nhien (diem se lac quan voi du lieu mo phong).
    """
    if mode == "split" and any(record.get("split") for record in records):
        train = [r for r in records if r.get("split") != "test"]
        test = [r for r in records if r.get("split") == "test"]
        if test:
            return train, test
        print("  (!) Không có bản ghi nào mang split=test, chuyển sang chế độ template.")
        mode = "template"

    from sklearn.model_selection import GroupShuffleSplit, train_test_split

    labels = [r["label"] for r in records]
    if mode == "template":
        groups = [str(r.get("template_id", r["id"])) for r in records]
        splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
        train_idx, test_idx = next(splitter.split(records, labels, groups=groups))
    else:
        train_idx, test_idx = train_test_split(
            range(len(records)), test_size=test_size, random_state=seed, stratify=labels
        )
    return [records[i] for i in train_idx], [records[i] for i in test_idx]


def source_counts(records: Sequence[dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for record in records:
        counts[record.get("source", "?")] = counts.get(record.get("source", "?"), 0) + 1
    return counts
