"""MODULE 4 - Unified Client API: gop Module 1 -> 2 -> 3 thanh mot luong duy nhat."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.classifier import analyze, build_badge_title, build_summary
from app.config import LEVEL_SAFE, THEME
from app.education import build_education
from app.preprocessor import PreprocessResult, preprocess


def quick_check(
    content: str,
    channel: Optional[str] = None,
    source_type: str = "raw_text",
    include_details: bool = False,
) -> Dict[str, Any]:
    """Chay toan trinh va tra ve payload hien thi cho client.

    Args:
        content: Noi dung tin nhan can kiem tra.
        channel: Kenh nhan tin (Zalo, Messenger, Discord, SMS...) - chi de thong ke.
        source_type: ``raw_text`` hoac ``screenshot``.
        include_details: Kem theo du lieu tho cua tung module (phuc vu demo/gioi thieu ky thuat).
    """
    started = time.perf_counter()

    pre: PreprocessResult = preprocess(content, source_type=source_type)
    analysis = analyze(pre=pre)
    education = build_education(analysis, seed=pre.cleaned_text)
    theme = THEME[analysis.risk_level]

    quiz = education["micro_learning"].get("quiz", {})
    result: Dict[str, Any] = {
        "verdict": {
            "level": analysis.risk_level,
            "badge_title": build_badge_title(analysis),
            "theme_color": theme["hex"],
            "emoji": theme["emoji"],
            "headline": theme["headline"],
            "confidence_score": analysis.confidence_score,
        },
        "summary": build_summary(analysis),
        "explanation": analysis.student_explanation,
        "highlight_words": analysis.highlight_words,
        "trigger_evidence": analysis.evidence,
        "immediate_actions": education["action_plan"]["steps"],
        "primary_warning": education["action_plan"]["primary_warning"],
        "flashcard": education["micro_learning"]["flashcard"],
        "interactive_quiz": {
            "quiz_id": quiz.get("quiz_id"),
            "question": quiz.get("question"),
            "options": quiz.get("options", []),
            "correct": quiz.get("correct_option"),
            "explanation": quiz.get("explanation"),
        },
        "meta": {
            "channel": channel,
            "scam_category": analysis.scam_category,
            "risk_score": analysis.risk_score,
            "engine": "+".join(
                ["rules"]
                + (["tfidf"] if analysis.ml_scores else [])
                + (["phobert"] if analysis.transformer_scores else [])
            ),
            "process_time_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }

    if analysis.risk_level == LEVEL_SAFE:
        result["highlight_words"] = []

    if include_details:
        result["details"] = {
            "module_1_preprocess": pre.to_dict(),
            "module_2_analysis": analysis.to_dict(),
            "module_3_education": education,
        }
    return result
