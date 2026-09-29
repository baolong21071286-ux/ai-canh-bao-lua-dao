"""MODULE 3 - Recommendation & Education Engine.

Anh xa ket qua phan loai cua Module 2 sang:
    * `action_plan`: canh bao chinh + cac buoc xu ly tuc thi.
    * `micro_learning`: 1 flashcard + 1 mini-quiz (~30 giay) de cung co ky nang.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from app.classifier import AnalysisResult
from app.config import (
    CATEGORY_SAFE,
    CATEGORY_TITLES,
    LEVEL_DANGEROUS,
    LEVEL_SAFE,
    LEVEL_SUSPICIOUS,
)
from app.education_content import CONTENT, GOLDEN_RULES

# Chi muc tra cuu nhanh: quiz_id -> noi dung quiz, card_id -> flashcard.
QUIZ_INDEX: Dict[str, Dict[str, Any]] = {
    quiz["quiz_id"]: {**quiz, "category": category}
    for category, block in CONTENT.items()
    for quiz in block["quizzes"]
}
FLASHCARD_INDEX: Dict[str, Dict[str, Any]] = {
    block["flashcard"]["card_id"]: {**block["flashcard"], "category": category}
    for category, block in CONTENT.items()
}


def _pick_quiz(quizzes: List[Dict[str, Any]], seed: str) -> Dict[str, Any]:
    """Chon quiz on dinh theo noi dung tin nhan.

    Cung mot tin nhan luon nhan cung mot cau hoi (de kiem thu va de demo),
    nhung cac tin nhan khac nhau se xoay vong qua nhieu cau hoi khac nhau.
    """
    if not quizzes:
        raise KeyError("Kich ban nay chua co mini-quiz.")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return quizzes[digest[0] % len(quizzes)]


def _primary_warning(level: str, base_warning: str) -> str:
    if level == LEVEL_DANGEROUS:
        return base_warning
    if level == LEVEL_SUSPICIOUS:
        return "HÃY CẨN THẬN: " + base_warning
    return base_warning


def build_education(analysis: AnalysisResult, seed: str = "", include_quiz: bool = True) -> Dict[str, Any]:
    """Sinh ke hoach hanh dong + noi dung hoc tap tu ket qua phan tich."""
    category = analysis.scam_category if analysis.scam_category in CONTENT else CATEGORY_SAFE
    if analysis.risk_level != LEVEL_SAFE and category == CATEGORY_SAFE:
        # Mo hinh ML thay dang ngo nhung bo luat chua chi ra duoc kich ban cu the.
        block = CONTENT["GENERIC_CAUTION"]
    else:
        block = CONTENT[category]
    seed = seed or " ".join(analysis.highlight_words) or category

    steps = list(block["steps"])
    if analysis.risk_level == LEVEL_DANGEROUS:
        # Voi muc do nguy hiem, nhac lai 3 nguyen tac vang o cuoi danh sach.
        steps = steps + [f"{len(steps) + 1}. Ghi nhớ: " + " ".join(GOLDEN_RULES)]

    payload: Dict[str, Any] = {
        "action_plan": {
            "primary_warning": block["primary_warning"]
            if block is CONTENT["GENERIC_CAUTION"]
            else _primary_warning(analysis.risk_level, block["primary_warning"]),
            "steps": steps,
            "scam_category": category,
            "scam_category_title": CATEGORY_TITLES.get(category, category),
        },
        "micro_learning": {
            "flashcard": dict(block["flashcard"]),
        },
    }
    if include_quiz:
        payload["micro_learning"]["quiz"] = dict(_pick_quiz(block["quizzes"], seed))
    return payload


def get_quiz(quiz_id: str) -> Optional[Dict[str, Any]]:
    return QUIZ_INDEX.get(quiz_id)


def check_answer(quiz_id: str, option_id: str) -> Dict[str, Any]:
    """Cham diem mot cau mini-quiz (dung cho giao dien tuong tac)."""
    quiz = QUIZ_INDEX.get(quiz_id)
    if quiz is None:
        raise KeyError(quiz_id)
    is_correct = str(option_id).strip().upper() == quiz["correct_option"]
    return {
        "quiz_id": quiz_id,
        "your_answer": str(option_id).strip().upper(),
        "correct_option": quiz["correct_option"],
        "is_correct": is_correct,
        "explanation": quiz["explanation"],
        "feedback": (
            "Chính xác! Em đã có phản xạ an toàn rất tốt."
            if is_correct
            else "Chưa đúng rồi. Em đọc kỹ phần giải thích bên dưới nhé!"
        ),
    }


def list_flashcards() -> List[Dict[str, Any]]:
    return list(FLASHCARD_INDEX.values())


def list_quizzes() -> List[Dict[str, Any]]:
    return list(QUIZ_INDEX.values())
