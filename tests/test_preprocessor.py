"""Kiem thu Module 1 - tien xu ly va trich xuat thuc the."""

import pytest

from app.preprocessor import PreprocessError, preprocess
from app.text_utils import deleet, fold, restore_diacritics


def test_cleaned_and_normalized_text():
    result = preprocess("Thầy Nam thể dục đây, nạp hộ thầy 2 thẻ Viettel 100k vào số này gấp.")
    assert result.cleaned_text.startswith("thay nam the duc day")
    assert "nạp hộ" in result.normalized_text
    assert result.metadata["source_type"] == "raw_text"
    assert result.metadata["word_count"] > 0


def test_restore_diacritics_for_input_without_accents():
    result = preprocess("thay nam the duc day, nap ho thay 2 the viettel 100k vao so nay gap")
    assert "thầy" in result.normalized_text
    assert "nạp" in result.normalized_text


def test_extract_entities():
    result = preprocess(
        "Chuyển gấp 500k vào số 0987654321 rồi bấm vào http://bit.ly/abc nhé, liên hệ a@b.com"
    )
    entities = result.entities
    assert "0987654321" in entities["phone_numbers"]
    assert any("bit.ly" in url for url in entities["urls"])
    assert "a@b.com" in entities["emails"]
    assert entities["urgency_markers"], "phải bắt được từ hối thúc 'gấp'"
    assert entities["financial_keywords"], "phải bắt được cụm từ tài chính"


def test_money_amount_is_not_a_phone_number():
    result = preprocess("Nạp giúp mình 100k nhé")
    assert result.entities["phone_numbers"] == []
    assert "100k" in result.entities["money_amounts"]


@pytest.mark.parametrize("bad_input", ["", "   ", "\n"])
def test_empty_input_raises(bad_input):
    with pytest.raises(PreprocessError):
        preprocess(bad_input)


def test_too_long_input_raises():
    with pytest.raises(PreprocessError):
        preprocess("a" * 2001)


def test_deleet_keeps_urls_and_numbers_intact():
    assert deleet(fold("nhap m4 0tp")) == "nhap ma otp"
    assert "192.168.10.5" in deleet(fold("tai ve tai http://192.168.10.5/x.apk"))
    assert "100k" in deleet(fold("nap 100k"))


def test_fold_handles_vietnamese_d():
    assert fold("Đừng nói với bố mẹ") == "dung noi voi bo me"


def test_restore_diacritics_is_lexicon_based():
    assert restore_diacritics("nap the gap") == "nạp thẻ gấp"
