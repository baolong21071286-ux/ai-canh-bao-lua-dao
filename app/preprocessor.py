"""MODULE 1 - Ingestion & Preprocessing.

Nhiem vu:
    1. Lam sach tin nhan (chuan hoa khoang trang, khu ky tu vo hinh, khu leet).
    2. Sinh `cleaned_text` (ASCII khong dau) va `normalized_text` (co dau, tach dau cau).
    3. Trich xuat thuc the: URL, so dien thoai, tu khoa tai chinh, tu thuc giuc...
"""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

from app.config import MAX_TEXT_LENGTH
from app.rules import ENTITY_SIGNALS, ALL_RULES
from app.text_utils import (
    deleet,
    fold_with_map,
    map_span,
    restore_diacritics,
    tokenize_for_display,
    word_count,
)

# --- Bieu thuc trich xuat thuc the ---
URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"'()\[\]]+"
    r"|(?<![@\w.])[a-z0-9][a-z0-9\-]{1,40}(?:\.[a-z0-9\-]{1,30})*"
    r"\.(?:com|vn|net|org|edu|gov|info|biz|vip|xyz|top|club|online|site|shop|store|icu|tk|ml|ga|gq|cf|buzz|win|me|io|co|app|link|fun|live)"
    r"(?:/[^\s<>\"'()\[\]]*)?",
    re.IGNORECASE,
)
# So dien thoai VN: bat dau 0 hoac +84, tong cong 9-11 chu so, cho phep dau phan cach.
PHONE_RE = re.compile(r"(?<![\w])(?:\+?84|0)(?:[\s.\-]?\d){8,10}(?![\w])")
EMAIL_RE = re.compile(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", re.IGNORECASE)
# So tien: 100k, 2 trieu, 500.000d, 50 nghin...
MONEY_RE = re.compile(
    r"(?<![\w])\d{1,3}(?:[.,]\d{3})*\s*(?:k|nghin|ngan|tram|trieu|tr|ty|vnd|vnđ|dong|đồng|d\b|đ\b)"
    r"|(?<![\w])\d+\s*(?:k|nghin|ngan|trieu|tr|ty)(?![\w])",
    re.IGNORECASE,
)
BANK_ACCOUNT_RE = re.compile(r"(?<![\w])\d{9,16}(?![\w])")
OTP_HINT_RE = re.compile(r"\b(otp|ma xac minh|ma xac nhan|ma bao mat|mat khau|password|pass)\b")


class PreprocessError(ValueError):
    """Loi dau vao khong hop le (rong, qua dai...)."""


@dataclass
class PreprocessResult:
    """Ket qua tien xu ly, dung lam dau vao cho Module 2."""

    original_text: str
    cleaned_text: str
    normalized_text: str
    #: Ban van ban dung de doi chieu luat (da fold + khu leet).
    match_text: str
    #: index_map[i] = vi tri ky tu match_text[i] trong original_text.
    index_map: List[int] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Xuat dung schema `data` cua endpoint `/api/v1/scan/preprocess`."""
        return {
            "cleaned_text": self.cleaned_text,
            "normalized_text": self.normalized_text,
            "extracted_entities": self.entities,
            "metadata": self.metadata,
        }


def has_diacritics(text: str) -> bool:
    """Kiem tra tin nhan goc da co dau tieng Viet hay chua."""
    for ch in unicodedata.normalize("NFD", text):
        if unicodedata.combining(ch):
            return True
    return "đ" in text.lower()


def _dedupe(items: Sequence[str]) -> List[str]:
    seen, out = set(), []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def _extract_keyword_entities(match_text: str, index_map: Sequence[int], original: str) -> Dict[str, List[str]]:
    """Trich cum tu tai chinh / thuc giuc bang chinh bo luat cua Module 2."""
    buckets: Dict[str, List[str]] = {name: [] for name in ENTITY_SIGNALS}
    for rule in ALL_RULES:
        targets = [name for name, signals in ENTITY_SIGNALS.items() if rule.signal in signals]
        if not targets:
            continue
        for pattern in rule.compiled:
            for m in pattern.finditer(match_text):
                phrase = map_span(match_text, index_map, m.start(), m.end(), original)
                if not phrase:
                    continue
                for name in targets:
                    buckets[name].append(phrase)
    return {name: _dedupe(values) for name, values in buckets.items()}


def preprocess(text: str, source_type: str = "raw_text") -> PreprocessResult:
    """Tien xu ly tin nhan tho thanh du lieu sach + thuc the.

    Args:
        text: Noi dung tin nhan (toi da 2000 ky tu theo dac ta).
        source_type: ``raw_text`` hoac ``screenshot`` (ghi vao metadata).

    Raises:
        PreprocessError: khi tin nhan rong hoac vuot qua gioi han do dai.
    """
    started = time.perf_counter()

    if text is None or not text.strip():
        raise PreprocessError("Nội dung tin nhắn đang trống. Em hãy dán tin nhắn cần kiểm tra nhé!")
    if len(text) > MAX_TEXT_LENGTH:
        raise PreprocessError(
            f"Tin nhắn dài {len(text)} ký tự, vượt quá giới hạn {MAX_TEXT_LENGTH} ký tự."
        )

    original = text.strip()
    folded, index_map = fold_with_map(original)
    match_text = deleet(folded)

    cleaned_text = folded
    if has_diacritics(original):
        normalized_text = tokenize_for_display(re.sub(r"\s+", " ", original.strip()).lower())
    else:
        normalized_text = tokenize_for_display(restore_diacritics(folded))

    keyword_entities = _extract_keyword_entities(match_text, index_map, original)
    urls = _dedupe(URL_RE.findall(original))
    phones = _dedupe([re.sub(r"[\s.\-]", "", p) for p in PHONE_RE.findall(original)])
    emails = _dedupe(EMAIL_RE.findall(original))
    money = _dedupe(MONEY_RE.findall(original))
    # So tai khoan: chuoi so dai khong phai so dien thoai va khong nam trong URL.
    bank_candidates = [
        b for b in BANK_ACCOUNT_RE.findall(original)
        if b not in phones and not b.startswith("0")
    ]

    entities: Dict[str, List[str]] = {
        "urls": urls,
        "phone_numbers": phones,
        "financial_keywords": keyword_entities.get("financial_keywords", []),
        "urgency_markers": keyword_entities.get("urgency_markers", []),
        "money_amounts": money,
        "emails": emails,
        "bank_accounts": _dedupe(bank_candidates),
        "otp_mentions": _dedupe(m.group(0) for m in OTP_HINT_RE.finditer(match_text)),
    }

    metadata = {
        "word_count": word_count(original),
        "char_count": len(original),
        "source_type": source_type,
        "has_diacritics": has_diacritics(original),
        "process_time_ms": round((time.perf_counter() - started) * 1000, 2),
    }

    return PreprocessResult(
        original_text=original,
        cleaned_text=cleaned_text,
        normalized_text=normalized_text,
        match_text=match_text,
        index_map=list(index_map),
        entities=entities,
        metadata=metadata,
    )


def rebuild_from_normalized(normalized_text: str, entities: Dict[str, List[str]] | None = None) -> PreprocessResult:
    """Dung lai `PreprocessResult` tu du lieu Module 1 da co.

    Phuc vu endpoint `/api/v1/scan/analyze` - noi client gui thang `normalized_text`
    (cung `extracted_entities`) ma khong goi lai buoc tien xu ly.
    """
    result = preprocess(normalized_text, source_type="normalized_text")
    if entities:
        for key, value in entities.items():
            if value:
                merged = _dedupe(list(result.entities.get(key, [])) + list(value))
                result.entities[key] = merged
    return result
