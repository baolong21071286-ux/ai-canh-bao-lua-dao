#!/usr/bin/env python3
"""Tai va chuyen doi cac bo du lieu tin nhan lua dao *thuc te* tu ben ngoai.

Vi sao can? Bo du lieu trong `data/` do nhom tu sinh nen diem danh gia tren do
lac quan hon thuc te. Cac bo du lieu duoi day do nguoi that thu thap va gan nhan,
dung lam **tap kiem dinh doc lap** - con so trung thuc de dua vao bao cao.

Du lieu tai ve nam trong `data/external/` va **khong duoc commit** vao kho ma nguon
(ton trong giay phep goc). Moi bo deu ghi ro nguon + giay phep trong `_meta.json`.

Cach dung::

    python scripts/fetch_external_datasets.py --list
    python scripts/fetch_external_datasets.py                 # tai bo mac dinh
    python scripts/fetch_external_datasets.py --name vi_sms_phishing
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATA_DIR, LEVEL_BY_LABEL  # noqa: E402

EXTERNAL_DIR = DATA_DIR / "external"
RAW_DIR = EXTERNAL_DIR / "raw"

# Bo du lieu goc da an danh PII bang cac token dang [PHONE], [MONEY]...
# De bo luat hoat dong nhu voi tin nhan that, ta "hoan nguyen" chung ve gia tri mau.
PLACEHOLDER_VALUES: Dict[str, str] = {
    "[PHONE]": "0987654321",
    "[BANK_ACC]": "19001234567",
    "[MONEY]": "500.000d",
    "[NUMBER]": "123456",
    "[TIME]": "15:30",
    "[DATE]": "20/09/2026",
    "[NAME]": "Nam",
    "[POINT]": "1000",
    "[URL]": "http://example.vip/abc",
}
# Token con lai thuong la nhan cua nguoi gui (vd "[TB]" = thong bao, "[QC]" = quang cao).
BRACKET_TOKEN_RE = re.compile(r"\[([A-Z_]{1,20})\]")


def rehydrate(text: str) -> str:
    """Thay token an danh bang gia tri mau de phan trich xuat thuc the hoat dong."""
    for token, value in PLACEHOLDER_VALUES.items():
        text = text.replace(token, value)
    return BRACKET_TOKEN_RE.sub(lambda m: m.group(1), text)


@dataclass
class ExternalDataset:
    """Mot bo du lieu ben ngoai + cach chuyen ve schema cua du an."""

    name: str
    title: str
    homepage: str
    license: str
    citation: str
    files: Dict[str, str]
    converter: Callable[[Dict[str, Path]], List[dict]]
    note: str = ""
    label_scheme: str = "binary"  # binary (0/2) hoac three_level (0/1/2)


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  (đã có) {dest.name}")
        return dest
    print(f"  tải {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "thcs-scam-detector/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, dest.open("wb") as fh:
        fh.write(response.read())
    return dest


def _read_csv(path: Path) -> List[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def convert_vi_sms(paths: Dict[str, Path]) -> List[dict]:
    """Bo SMS lua dao tieng Viet: nhan nhi phan 0 = hop le, 1 = rac/lua dao.

    Nhan 1 duoc anh xa sang muc 2 (DANGEROUS) cua he thong. Vi nhan goc gop chung
    ca "rac" lan "lua dao", viec danh gia nen chay o **che do nhi phan**
    (`scripts/evaluate.py --binary`): coi 🟡 va 🔴 deu la "co canh bao".
    """
    records: List[dict] = []
    for split, path in paths.items():
        for index, row in enumerate(_read_csv(path), start=1):
            message = (row.get("message") or "").strip()
            raw_label = (row.get("label") or "").strip()
            if not message or raw_label not in {"0", "1"}:
                continue
            label = 2 if raw_label == "1" else 0
            records.append(
                {
                    "id": f"EXT_VISMS_{split.upper()}_{index:05d}",
                    "text": rehydrate(message),
                    "label": label,
                    "label_name": LEVEL_BY_LABEL[label],
                    "category": "EXTERNAL_SMS",
                    "template_id": f"EXT_{split}",
                    "split": split,
                    "original_label": int(raw_label),
                    "risk_entities": [],
                }
            )
    return records


REGISTRY: List[ExternalDataset] = [
    ExternalDataset(
        name="vi_sms_phishing",
        title="Quality-Assured Vietnamese SMS Phishing Dataset (2.991 mẫu)",
        homepage="https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_dataset",
        license="CC BY 4.0",
        citation=(
            "Tran, N. T. T.; Le, H. K.; Nguyen, M. T.; Nguyen, V. T.; Mai, H. D. "
            "Vietnamese SMS Dataset with Quality Assurance. IEEE Access, 2026."
        ),
        files={
            "train": "https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_dataset/resolve/main/train.csv",
            "test": "https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_dataset/resolve/main/test.csv",
        },
        converter=convert_vi_sms,
        note=(
            "Tin nhắn SMS thật của người Việt, đã ẩn danh PII, gán nhãn nhị phân. "
            "Chủ đề thiên về ngân hàng/viễn thông (người lớn) nên KHÁC miền với tin nhắn "
            "học sinh THCS — dùng để kiểm tra độ bền, không phải để thay thế dữ liệu học đường."
        ),
    ),
    ExternalDataset(
        name="vi_sms_phishing_sample",
        title="Vietnamese SMS phishing — bản mẫu 300 tin",
        homepage="https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_phishing_sample",
        license="CC BY 4.0",
        citation="Cùng nhóm tác giả với bộ vi_sms_phishing.",
        files={
            "sample": "https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_phishing_sample/resolve/main/sample_300.csv",
        },
        converter=convert_vi_sms,
        note="Bản rút gọn, tiện để chạy thử nhanh.",
    ),
]

REGISTRY_BY_NAME = {dataset.name: dataset for dataset in REGISTRY}
DEFAULT_DATASETS = ["vi_sms_phishing"]


def fetch(dataset: ExternalDataset) -> Path:
    print(f"\n### {dataset.name} — {dataset.title}")
    print(f"  giấy phép: {dataset.license} | nguồn: {dataset.homepage}")
    paths = {
        split: _download(url, RAW_DIR / dataset.name / Path(url).name)
        for split, url in dataset.files.items()
    }
    records = dataset.converter(paths)

    out_path = EXTERNAL_DIR / f"{dataset.name}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    meta = {
        "name": dataset.name,
        "title": dataset.title,
        "homepage": dataset.homepage,
        "license": dataset.license,
        "citation": dataset.citation,
        "note": dataset.note,
        "label_scheme": dataset.label_scheme,
        "records": len(records),
        "label_counts": {
            LEVEL_BY_LABEL[label]: sum(1 for r in records if r["label"] == label)
            for label in sorted({r["label"] for r in records})
        },
    }
    (EXTERNAL_DIR / f"{dataset.name}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  → {out_path} ({len(records)} mẫu) | {meta['label_counts']}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Tải bộ dữ liệu tin nhắn lừa đảo thực tế")
    parser.add_argument("--name", action="append", help="Tên bộ dữ liệu (lặp lại được)")
    parser.add_argument("--all", action="store_true", help="Tải tất cả bộ trong danh mục")
    parser.add_argument("--list", action="store_true", help="Liệt kê danh mục rồi thoát")
    args = parser.parse_args()

    if args.list:
        for dataset in REGISTRY:
            print(f"{dataset.name:26s} {dataset.license:12s} {dataset.title}")
            print(f"{'':26s} {dataset.homepage}")
            if dataset.note:
                print(f"{'':26s} {dataset.note}")
        return

    names = args.name or (list(REGISTRY_BY_NAME) if args.all else DEFAULT_DATASETS)
    for name in names:
        if name not in REGISTRY_BY_NAME:
            raise SystemExit(f"Không có bộ dữ liệu `{name}`. Chạy --list để xem danh mục.")
        fetch(REGISTRY_BY_NAME[name])

    print(
        "\nLưu ý: dữ liệu ngoài nằm trong data/external/ và KHÔNG được commit. "
        "Khi dùng trong báo cáo, hãy trích dẫn đúng nguồn ghi trong tệp *_meta.json."
    )


if __name__ == "__main__":
    main()
