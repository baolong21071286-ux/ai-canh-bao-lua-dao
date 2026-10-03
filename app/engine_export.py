"""Xuat toan bo tri thuc cua he thong (luat, nguong, noi dung giao duc) ra JSON.

Duoc dung boi:
    * `scripts/build_static_site.py` - dung ban demo tinh cho GitHub Pages.
    * `app/main.py` - phuc vu endpoint `/engine-data.json` cho giao dien web.

Nho vay ban chay tren may chu va ban chay trong trinh duyet luon dung CHUNG mot
bo luat duy nhat.
"""

from __future__ import annotations

from app.classifier import (
    COMBOS,
    EXPLANATION_TEMPLATES,
    RULE_SUPPRESSIONS,
    IDENTITY_ONLY_SIGNALS,
    STANDALONE_SIGNALS,
    RISK_SIGNALS,
    SUMMARY_TEMPLATES,
)
from app.config import (
    API_VERSION,
    BASE_DIR,
    CATEGORY_PRIORITY,
    CATEGORY_TITLES,
    FRONTEND_DIR,
    ML_WEIGHT,
    MODEL_SAFE_VETO,
    MODEL_SAFE_VETO_FACTOR,
    RULE_WEIGHT,
    THEME,
    THRESHOLD_DANGEROUS,
    THRESHOLD_SUSPICIOUS,
    TRANSFORMER_WEIGHT,
)
from app.domains import (
    BRAND_TOKENS,
    MULTI_LABEL_SUFFIXES,
    OFFICIAL_DOMAINS,
    RISKY_TLDS,
    URL_IN_TEXT_RE,
    load_blocklist,
)
from app.education_content import CONTENT, GOLDEN_RULES
from app.link_analyzer import SHORTENERS
from app.rules import ALL_RULES

# JavaScript dung `\w` theo kieu ASCII, con Python coi ca chu co dau la ky tu tu.
# Neu khong chinh lai, trinh duyet se cat nham "...toizalo.me" thanh mot ten mien.
JS_WORD_BOUNDARY_FIX = {
    r"(?<![@\w.])": r"(?<![@.\w\u00C0-\u024F\u1E00-\u1EFF])",
}


def to_js_pattern(pattern: str) -> str:
    """Chuyen bieu thuc chinh quy cua Python sang ban tuong duong chay dung tren JS."""
    for old, new in JS_WORD_BOUNDARY_FIX.items():
        pattern = pattern.replace(old, new)
    return pattern


def build_engine_data() -> dict:
    """Gom toan bo tri thuc cua he thong thanh mot tep JSON cho trinh duyet."""
    return {
        "version": API_VERSION,
        "thresholds": {"dangerous": THRESHOLD_DANGEROUS, "suspicious": THRESHOLD_SUSPICIOUS},
        "theme": THEME,
        "categoryTitles": CATEGORY_TITLES,
        "categoryPriority": CATEGORY_PRIORITY,
        "riskSignals": sorted(RISK_SIGNALS),
        "standaloneSignals": sorted(STANDALONE_SIGNALS),
        "modelWeights": {"rule": RULE_WEIGHT, "ml": ML_WEIGHT, "transformer": TRANSFORMER_WEIGHT},
        "modelSafeVeto": MODEL_SAFE_VETO,
        "modelSafeVetoFactor": MODEL_SAFE_VETO_FACTOR,
        "identityOnlySignals": sorted(IDENTITY_ONLY_SIGNALS),
        "suppressions": {k: sorted(v) for k, v in RULE_SUPPRESSIONS.items()},
        "urlPattern": to_js_pattern(URL_IN_TEXT_RE.pattern),
        "rules": [
            {
                "id": rule.id,
                "signal": rule.signal,
                "category": rule.category,
                "weight": rule.weight,
                "reason": rule.reason,
                "patterns": [to_js_pattern(p) for p in rule.patterns],
                "hardDanger": rule.hard_danger,
                "amplifier": rule.amplifier,
                "standalone": rule.standalone,
            }
            for rule in ALL_RULES
        ],
        "combos": [
            {
                "id": combo.id,
                "requires": [sorted(group) for group in combo.requires],
                "category": combo.category,
                "boost": combo.boost,
                "reason": combo.reason,
                "hardDanger": combo.hard_danger,
                "definesCategory": combo.defines_category,
            }
            for combo in COMBOS
        ],
        "domains": {
            "official": sorted(OFFICIAL_DOMAINS),
            "brands": sorted(BRAND_TOKENS),
            "riskyTlds": sorted(RISKY_TLDS),
            "shorteners": sorted(SHORTENERS),
            "multiSuffixes": sorted(MULTI_LABEL_SUFFIXES),
            # Danh sach den (neu da tai ve) duoc gui kem de ban chay trong trinh duyet
            # co cung tri thuc voi may chu. Gioi han so luong de trang khong nang.
            "blocklist": sorted(load_blocklist())[:20000],
        },
        "explanations": EXPLANATION_TEMPLATES,
        "summaries": SUMMARY_TEMPLATES,
        "education": CONTENT,
        "goldenRules": GOLDEN_RULES,
    }