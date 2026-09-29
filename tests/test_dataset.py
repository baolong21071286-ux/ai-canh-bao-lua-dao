"""Kiem thu bo du lieu: dung dinh dang JSONL va dung co cau 40/20/40 theo dac ta."""

import json
from collections import Counter

import pytest

from app.config import DATASET_DEMO, DATASET_FULL, LEVEL_BY_LABEL

REQUIRED_FIELDS = {"id", "text", "label", "label_name", "category", "risk_entities"}


def load(path):
    if not path.exists():
        pytest.skip(f"Chưa sinh {path.name}. Chạy: python data/generate_sample_dataset.py")
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


@pytest.mark.parametrize("path", [DATASET_DEMO, DATASET_FULL])
def test_records_are_well_formed(path):
    records = load(path)
    ids = set()
    for record in records:
        assert REQUIRED_FIELDS <= set(record), record.get("id")
        assert record["text"].strip()
        assert record["label"] in (0, 1, 2)
        assert record["label_name"] == LEVEL_BY_LABEL[record["label"]]
        assert record["id"] not in ids, "id phải là duy nhất"
        ids.add(record["id"])


@pytest.mark.parametrize("path", [DATASET_DEMO, DATASET_FULL])
def test_label_distribution_matches_specification(path):
    """Dac ta Muc 4.1: 40% an toan - 20% nghi van - 40% nguy hiem."""
    records = load(path)
    counts = Counter(record["label"] for record in records)
    total = len(records)
    assert counts[0] / total == pytest.approx(0.4, abs=0.02)
    assert counts[1] / total == pytest.approx(0.2, abs=0.02)
    assert counts[2] / total == pytest.approx(0.4, abs=0.02)


def test_demo_set_has_sixty_samples():
    """Dac ta Muc 7, Giai doan 1: bo demo gom 60 mau."""
    assert len(load(DATASET_DEMO)) == 60


def test_full_set_size_in_specified_range():
    """Dac ta Muc 4.1: quy mo mau thu nghiem 1.500 - 3.000."""
    assert 1500 <= len(load(DATASET_FULL)) <= 3000


def test_texts_are_unique():
    records = load(DATASET_FULL)
    texts = [record["text"].lower() for record in records]
    assert len(texts) == len(set(texts))
