"""Kiem thu Module 3 - hanh dong khuyen nghi, flashcard va mini-quiz."""

import pytest

from app.classifier import analyze
from app.config import CATEGORY_TITLES, LEVEL_DANGEROUS
from app.education import QUIZ_INDEX, build_education, check_answer, list_flashcards
from app.education_content import CONTENT


def test_every_category_has_content():
    """Moi kich ban lua dao deu phai co noi dung giao duc tuong ung."""
    for category in CATEGORY_TITLES:
        assert category in CONTENT, f"Thiếu nội dung giáo dục cho {category}"


def test_content_blocks_are_well_formed():
    for category, block in CONTENT.items():
        assert block["primary_warning"].strip()
        assert block["steps"], category
        assert block["flashcard"]["card_id"] and block["flashcard"]["tip"]
        assert block["quizzes"], category
        for quiz in block["quizzes"]:
            ids = {option["id"] for option in quiz["options"]}
            assert len(quiz["options"]) >= 3
            assert quiz["correct_option"] in ids, quiz["quiz_id"]
            assert quiz["explanation"].strip()


def test_quiz_ids_are_unique():
    all_ids = [quiz["quiz_id"] for block in CONTENT.values() for quiz in block["quizzes"]]
    assert len(all_ids) == len(set(all_ids))


def test_card_ids_are_unique():
    cards = [card["card_id"] for card in list_flashcards()]
    assert len(cards) == len(set(cards))


def test_build_education_for_dangerous_message():
    analysis = analyze("Thầy Nam đây, nạp hộ thầy 2 thẻ Viettel 100k gấp.", use_ml=False)
    payload = build_education(analysis, seed="demo")
    assert analysis.risk_level == LEVEL_DANGEROUS
    assert payload["action_plan"]["primary_warning"]
    assert len(payload["action_plan"]["steps"]) >= 3
    assert payload["micro_learning"]["flashcard"]["title"]
    assert payload["micro_learning"]["quiz"]["question"]


def test_quiz_choice_is_stable_for_same_message():
    analysis = analyze("Nhập mã OTP để nhận Robux miễn phí nhé.", use_ml=False)
    first = build_education(analysis, seed="cùng một tin nhắn")
    second = build_education(analysis, seed="cùng một tin nhắn")
    assert first["micro_learning"]["quiz"]["quiz_id"] == second["micro_learning"]["quiz"]["quiz_id"]


def test_check_answer_correct_and_incorrect():
    quiz_id = "QZ_OTP_01"
    correct = QUIZ_INDEX[quiz_id]["correct_option"]
    assert check_answer(quiz_id, correct)["is_correct"] is True
    wrong = next(o["id"] for o in QUIZ_INDEX[quiz_id]["options"] if o["id"] != correct)
    result = check_answer(quiz_id, wrong)
    assert result["is_correct"] is False
    assert result["explanation"]


def test_check_answer_is_case_insensitive():
    assert check_answer("QZ_OTP_01", "b")["your_answer"] == "B"


def test_unknown_quiz_raises():
    with pytest.raises(KeyError):
        check_answer("KHONG_TON_TAI", "A")
