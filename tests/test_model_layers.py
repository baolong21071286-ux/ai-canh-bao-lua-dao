"""Kiem thu cac lop mo hinh tuy chon va co che xuat du lieu cho ban chay offline.

Nguyen tac quan trong: **thieu lop nao he thong van phai chay duoc**. Nguoi tai kho
ma nguon ve chua huan luyen gi ca van dung duoc ngay bang bo luat.
"""

from __future__ import annotations

import json

import pytest

from app import ml_model, transformer_model
from app.classifier import analyze
from app.config import LEVEL_DANGEROUS, LEVEL_SAFE
from app.engine_export import build_engine_data, to_js_pattern


def test_system_works_without_any_model():
    """Khong dung lop ML nao thi van phan loai duoc."""
    result = analyze("Thầy Nam đây, nạp hộ thầy 2 thẻ Viettel 100k gấp nhé.", use_ml=False)
    assert result.risk_level == LEVEL_DANGEROUS
    assert result.ml_scores is None
    assert result.transformer_scores is None
    assert result.evidence


def test_transformer_layer_is_optional():
    """Chua huan luyen PhoBERT thi ham tra ve None chu khong duoc bao loi."""
    scores = transformer_model.predict_proba("nạp hộ thầy 100k gấp")
    assert scores is None or isinstance(scores, dict)
    if isinstance(scores, dict):
        assert abs(sum(scores.values()) - 1.0) < 0.01


def test_ml_layer_is_optional():
    scores = ml_model.predict_proba("nap ho thay 100k gap")
    assert scores is None or isinstance(scores, dict)


def test_engine_label_reflects_available_layers():
    from app.pipeline import quick_check

    engine = quick_check("Mai nhớ mang vở bài tập Toán nhé!")["meta"]["engine"]
    assert engine.startswith("rules")
    if ml_model.is_available():
        assert "tfidf" in engine
    if transformer_model.is_available():
        assert "phobert" in engine


# --- Xuat du lieu cho ban chay trong trinh duyet ---
def test_engine_data_is_complete_and_serializable():
    data = build_engine_data()
    for key in ("rules", "combos", "education", "theme", "thresholds", "domains", "urlPattern"):
        assert key in data, key
    assert data["rules"] and data["combos"] and data["education"]
    json.dumps(data, ensure_ascii=False)  # phải chuyển được sang JSON


def test_every_rule_exports_its_explanation():
    for rule in build_engine_data()["rules"]:
        assert rule["reason"].strip(), rule["id"]
        assert rule["patterns"], rule["id"]


def test_js_pattern_conversion_fixes_word_boundary():
    """JavaScript hiểu `\\w` theo kiểu ASCII nên phải nới lookbehind cho chữ có dấu."""
    converted = to_js_pattern(r"(?<![@\w.])abc")
    assert "\\u00C0-\\u024F" in converted
    assert to_js_pattern(r"\bnap ho\b") == r"\bnap ho\b"


def test_education_content_covers_every_exported_category():
    data = build_engine_data()
    categories = {rule["category"] for rule in data["rules"]} | {c["category"] for c in data["combos"]}
    for category in categories:
        assert category in data["education"] or category == "SAFE", category


def test_safe_message_stays_safe_with_all_layers():
    assert analyze("Mai nhớ mang vở bài tập Toán nhé, cô kiểm tra 15 phút đấy!").risk_level == LEVEL_SAFE
