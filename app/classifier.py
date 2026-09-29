"""MODULE 2 - AI Classification & Explainability Engine.

Kien truc lai (hybrid):
    (a) **Bo luat regex co trong so** -> cho ra diem rui ro *va* bang chung giai thich duoc.
    (b) **Luat ket hop (combo)** -> mo phong cach suy luan cua con nguoi, vi du
        "mao danh thay co" + "doi nap the" = gan nhu chac chan lua dao.
    (c) **Mo hinh TF-IDF/Linear** (neu da huan luyen) -> bat cac cach dien dat moi.

Dau ra tuan thu schema `analysis` trong dac ta ky thuat (Muc 3, Module 2).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from app import ml_model, transformer_model
from app.config import (
    CATEGORY_ACCOUNT_THREAT,
    CATEGORY_GAMBLING,
    CATEGORY_ADS_SPAM,
    CATEGORY_FAKE_PRIZE,
    CATEGORY_GAME_TOPUP,
    CATEGORY_IMPERSONATION_RELATIVE,
    CATEGORY_IMPERSONATION_TEACHER,
    CATEGORY_JOB_SCAM,
    CATEGORY_OTP_PHISHING,
    CATEGORY_PHISHING_LINK,
    CATEGORY_PRIORITY,
    CATEGORY_SAFE,
    CATEGORY_SUSPICIOUS_INVITE,
    CATEGORY_TITLES,
    LEVEL_DANGEROUS,
    LEVEL_SAFE,
    LEVEL_SUSPICIOUS,
    ML_WEIGHT,
    MODEL_SAFE_VETO,
    MODEL_SAFE_VETO_FACTOR,
    RULE_WEIGHT,
    TRANSFORMER_WEIGHT,
    THEME,
    THRESHOLD_DANGEROUS,
    THRESHOLD_SUSPICIOUS,
)
from app.link_analyzer import LinkHit, analyze_links
from app.preprocessor import PreprocessResult, preprocess
from app.rules import (
    ALL_RULES,
    SIG_ADS,
    SIG_FREEBIE,
    SIG_IMPERSONATION,
    SIG_INVITE,
    SIG_JOB,
    SIG_LINK,
    SIG_MONEY,
    SIG_OTP,
    SIG_PRIZE,
    SIG_SAFE,
    SIG_SECRECY,
    SIG_THREAT,
    SIG_URGENCY,
    Rule,
)
from app.text_utils import map_span

MAX_EVIDENCE = 5

# Cau giai thich tong the theo tung kich ban, viet cho hoc sinh THCS de hieu.
EXPLANATION_TEMPLATES: Dict[str, str] = {
    CATEGORY_GAMBLING: (
        "Tin nhắn dụ nạp tiền vào trang cờ bạc/đổi thưởng trá hình. "
        "Những trang này luôn cho thắng vài ván đầu rồi chiếm sạch tiền — và học sinh tham gia là vi phạm pháp luật."
    ),
    CATEGORY_IMPERSONATION_TEACHER: (
        "Tin nhắn này có dấu hiệu giả mạo thầy cô giáo để nhờ nạp tiền hoặc chuyển khoản. "
        "Thầy cô không bao giờ nhắn tin nhờ học sinh mua thẻ cào hay chuyển tiền qua mạng xã hội."
    ),
    CATEGORY_IMPERSONATION_RELATIVE: (
        "Tin nhắn này có dấu hiệu giả mạo người thân hoặc bạn bè để hỏi vay tiền. "
        "Tài khoản của người quen rất dễ bị chiếm đoạt, vì vậy hãy gọi điện trực tiếp để kiểm chứng."
    ),
    CATEGORY_GAME_TOPUP: (
        "Đây là chiêu dụ nạp thẻ / tặng vật phẩm game miễn phí. "
        "Không có sự kiện chính thức nào bắt em nạp tiền trước hoặc đưa tài khoản để nhận quà."
    ),
    CATEGORY_FAKE_PRIZE: (
        "Tin nhắn thông báo trúng thưởng nhưng đòi nộp phí hoặc bấm link lạ. "
        "Phần thưởng thật không bao giờ yêu cầu em trả tiền trước."
    ),
    CATEGORY_OTP_PHISHING: (
        "Tin nhắn lừa đảo nhằm chiếm đoạt mã OTP / mật khẩu của em. "
        "Mã OTP là chìa khóa tài khoản, tuyệt đối không đọc hay gửi cho bất kỳ ai."
    ),
    CATEGORY_ACCOUNT_THREAT: (
        "Tin nhắn mang tính đe dọa, tống tiền hoặc dọa chiếm tài khoản để làm em hoảng sợ. "
        "Kẻ xấu muốn em im lặng làm theo — hãy kể ngay với bố mẹ, thầy cô."
    ),
    CATEGORY_PHISHING_LINK: (
        "Tin nhắn chứa đường link lạ có thể dẫn tới trang giả mạo để đánh cắp tài khoản. "
        "Không bấm vào link khi chưa kiểm chứng với người lớn."
    ),
    CATEGORY_JOB_SCAM: (
        "Lời mời 'việc nhẹ lương cao' dành cho học sinh hầu hết là bẫy lừa đảo, "
        "cuối cùng sẽ yêu cầu em nộp tiền hoặc làm nhiệm vụ chuyển khoản."
    ),
    CATEGORY_SUSPICIOUS_INVITE: (
        "Tin nhắn mời vào nhóm/kênh lạ chưa rõ mục đích. "
        "Trong các nhóm này người lạ có thể tiếp cận và dụ dỗ em, hãy hỏi ý kiến người lớn trước."
    ),
    CATEGORY_ADS_SPAM: (
        "Tin nhắn quảng cáo gửi tới số máy cá nhân, chưa rõ nguồn gốc. "
        "Chưa thấy dấu hiệu chiếm đoạt tiền nhưng em không nên bấm link hay để lại thông tin."
    ),
    CATEGORY_SAFE: (
        "Tin nhắn có nội dung trao đổi bình thường, không thấy dấu hiệu lừa đảo. "
        "Em vẫn nên cảnh giác nếu sau đó có ai hỏi tiền, mã OTP hay mật khẩu."
    ),
}


@dataclass
class RuleHit:
    """Mot luat duoc kich hoat cung cac doan van ban lam bang chung."""

    rule: Rule
    phrases: List[str] = field(default_factory=list)

    @property
    def phrase(self) -> str:
        return self.phrases[0] if self.phrases else ""


@dataclass
class Combo:
    """Luat ket hop nhieu tin hieu."""

    id: str
    requires: Tuple[Set[str], ...]
    category: str
    boost: float
    reason: str
    hard_danger: bool = False
    #: Combo "bo tro" chi cong diem, khong dung de dat ten kich ban lua dao.
    defines_category: bool = True


# Cac to hop "kinh dien" trong kich ban lua dao hoc duong.
COMBOS: List[Combo] = [
    Combo(
        id="COMBO_IMPERSONATION_MONEY",
        requires=({SIG_IMPERSONATION}, {SIG_MONEY}),
        category=CATEGORY_IMPERSONATION_TEACHER,
        boost=0.45,
        hard_danger=True,
        reason="Vừa tự xưng là người quen, vừa hỏi tiền/thẻ cào — mẫu lừa đảo mạo danh điển hình.",
    ),
    Combo(
        id="COMBO_IMPERSONATION_OTP",
        requires=({SIG_IMPERSONATION}, {SIG_OTP}),
        category=CATEGORY_OTP_PHISHING,
        boost=0.45,
        hard_danger=True,
        reason="Tự xưng người quen rồi hỏi mã OTP/mật khẩu — chắc chắn là chiêu chiếm tài khoản.",
    ),
    Combo(
        id="COMBO_FREEBIE_ACTION",
        requires=({SIG_FREEBIE}, {SIG_LINK, SIG_MONEY, SIG_OTP}),
        category=CATEGORY_GAME_TOPUP,
        boost=0.4,
        hard_danger=True,
        reason="Hứa tặng đồ miễn phí nhưng lại bắt bấm link / nạp tiền / đưa tài khoản.",
    ),
    Combo(
        id="COMBO_PRIZE_FEE",
        requires=({SIG_PRIZE}, {SIG_MONEY, SIG_LINK}),
        category=CATEGORY_FAKE_PRIZE,
        boost=0.4,
        hard_danger=True,
        reason="Báo trúng thưởng kèm yêu cầu nộp phí hoặc bấm link — quà thật không thu phí.",
    ),
    Combo(
        id="COMBO_SECRECY_MONEY",
        requires=({SIG_SECRECY}, {SIG_MONEY, SIG_OTP, SIG_LINK}),
        category=CATEGORY_ACCOUNT_THREAT,
        boost=0.4,
        hard_danger=True,
        reason="Bắt giấu bố mẹ khi làm việc liên quan tới tiền/tài khoản — không bao giờ là việc tử tế.",
        defines_category=False,
    ),
    Combo(
        id="COMBO_MONEY_URGENCY",
        requires=({SIG_MONEY}, {SIG_URGENCY}),
        category=CATEGORY_IMPERSONATION_RELATIVE,
        boost=0.25,
        reason="Hỏi tiền kèm hối thúc gấp gáp để em không kịp hỏi người lớn.",
        defines_category=False,
    ),
    Combo(
        id="COMBO_LINK_LURE",
        requires=({SIG_LINK}, {SIG_FREEBIE, SIG_PRIZE, SIG_JOB, SIG_THREAT}),
        category=CATEGORY_PHISHING_LINK,
        boost=0.3,
        reason="Link lạ đi kèm mồi nhử quà tặng/phần thưởng — thường là trang web giả mạo.",
    ),
    Combo(
        id="COMBO_INVITE_LINK",
        requires=({SIG_INVITE}, {SIG_LINK}),
        category=CATEGORY_SUSPICIOUS_INVITE,
        boost=0.1,
        reason="Lời mời vào nhóm kèm link lạ, chưa rõ ai quản lý nhóm đó.",
    ),
    Combo(
        id="COMBO_JOB_MONEY",
        requires=({SIG_JOB}, {SIG_MONEY, SIG_LINK}),
        category=CATEGORY_JOB_SCAM,
        boost=0.3,
        hard_danger=True,
        reason="Mời làm việc kiếm tiền rồi dẫn tới nạp tiền/bấm link — bẫy 'việc nhẹ lương cao'.",
    ),
]

#: Luat "khu nhieu": khi luat ben trai khop thi cac luat ben phai bi vo hieu.
#: Vi du: ngan hang *thong bao* ma OTP cho chinh chu tai khoan khac han voi viec
#: mot nguoi la *hoi xin* ma OTP - neu khong tach hai truong hop nay, he thong
#: bao do toan bo tin nhan OTP hop le (do duoc tren du lieu SMS that).
RULE_SUPPRESSIONS: Dict[str, Set[str]] = {
    "SAFE_OTP_NOTIFICATION": {"OTP_REQUEST", "OTP_PASSWORD_REQUEST"},
}

RISK_SIGNALS = {
    SIG_IMPERSONATION,
    SIG_MONEY,
    SIG_OTP,
    SIG_THREAT,
    SIG_FREEBIE,
    SIG_PRIZE,
    SIG_LINK,
    SIG_JOB,
    SIG_INVITE,
    SIG_ADS,
    SIG_SECRECY,
    SIG_URGENCY,
}
# Tin hieu du suc mot minh ket luan co rui ro (khong can luat khac di kem).
STANDALONE_SIGNALS = {SIG_OTP, SIG_THREAT, SIG_SECRECY, SIG_MONEY, SIG_PRIZE, SIG_JOB, SIG_FREEBIE}


@dataclass
class AnalysisResult:
    """Ket qua phan tich cua Module 2."""

    risk_level: str
    risk_score: float
    confidence_score: float
    scam_category: str
    evidence: List[Dict[str, str]]
    student_explanation: str
    highlight_words: List[str]
    matched_rules: List[str]
    signals: List[str]
    rule_score: float
    ml_scores: Optional[Dict[str, float]]
    process_time_ms: float
    transformer_scores: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Xuat dung schema `analysis` trong dac ta ky thuat."""
        theme = THEME[self.risk_level]
        return {
            "risk_level": self.risk_level,
            "risk_color": theme["color_name"],
            "confidence_score": self.confidence_score,
            "scam_category": self.scam_category,
            "scam_category_title": CATEGORY_TITLES.get(self.scam_category, self.scam_category),
            "trigger_evidence": self.evidence,
            "student_explanation": self.student_explanation,
            "highlight_words": self.highlight_words,
            "debug": {
                "risk_score": self.risk_score,
                "rule_score": self.rule_score,
                "ml_scores": self.ml_scores,
                "transformer_scores": self.transformer_scores,
                "matched_rules": self.matched_rules,
                "signals": self.signals,
                "process_time_ms": self.process_time_ms,
            },
        }


def _noisy_or(weights: Sequence[float]) -> float:
    """Gop nhieu bang chung doc lap: 1 - tich(1 - w). Luon nam trong [0, 1)."""
    acc = 1.0
    for w in weights:
        acc *= 1.0 - max(0.0, min(1.0, w))
    return 1.0 - acc


def _link_hits_to_rule_hits(link_hits: List[LinkHit]) -> List[RuleHit]:
    """Dua ket qua phan tich ten mien ve cung dinh dang voi luat regex."""
    hits: List[RuleHit] = []
    for link in link_hits:
        rule = Rule(
            id=link.rule_id,
            signal=SIG_LINK,
            category=link.category,
            weight=link.weight,
            reason=link.reason,
            patterns=(),
            hard_danger=link.hard_danger,
            standalone=link.standalone,
        )
        hits.append(RuleHit(rule=rule, phrases=[link.url]))
    return hits


def _collect_hits(pre: PreprocessResult) -> List[RuleHit]:
    """Chay toan bo bo luat tren van ban da chuan hoa."""
    hits: List[RuleHit] = []
    for rule in ALL_RULES:
        phrases: List[str] = []
        for pattern in rule.compiled:
            for m in pattern.finditer(pre.match_text):
                phrase = map_span(pre.match_text, pre.index_map, m.start(), m.end(), pre.original_text)
                if phrase and phrase.lower() not in {p.lower() for p in phrases}:
                    phrases.append(phrase)
        if phrases:
            hits.append(RuleHit(rule=rule, phrases=phrases))
    return hits


def _pick_category(risk_hits: List[RuleHit], combo_hits: List[Combo]) -> str:
    """Chon kich ban lua dao: uu tien combo hard-danger, sau do la do uu tien danh muc."""
    # Bang chung "chac chan" (hard danger) duoc uu tien truoc, trong do chon
    # danh muc co do uu tien cao nhat: doi OTP > de doa > mao danh > qua tang...
    hard_candidates = [c.category for c in combo_hits if c.hard_danger and c.defines_category]
    hard_candidates += [h.rule.category for h in risk_hits if h.rule.hard_danger]
    if hard_candidates:
        return max(hard_candidates, key=lambda cat: CATEGORY_PRIORITY.get(cat, 0))

    scores: Dict[str, float] = {}
    for hit in risk_hits:
        if hit.rule.category == CATEGORY_SAFE:
            continue
        scores[hit.rule.category] = scores.get(hit.rule.category, 0.0) + hit.rule.weight
    for combo in combo_hits:
        if combo.defines_category:
            scores[combo.category] = scores.get(combo.category, 0.0) + combo.boost
    if not scores:
        return CATEGORY_SAFE
    return max(scores.items(), key=lambda kv: (kv[1], CATEGORY_PRIORITY.get(kv[0], 0)))[0]


def _build_evidence(risk_hits: List[RuleHit], combos: List[Combo], category: str) -> List[Dict[str, str]]:
    """Chon toi da MAX_EVIDENCE bang chung, uu tien luat thuoc dung kich ban da chon."""
    ordered = sorted(
        risk_hits,
        key=lambda h: (
            h.rule.category == category,
            h.rule.hard_danger,
            h.rule.weight,
        ),
        reverse=True,
    )
    evidence: List[Dict[str, str]] = []
    seen_phrases: Set[str] = set()
    for hit in ordered:
        phrase = hit.phrase
        key = phrase.lower()
        if not phrase or key in seen_phrases:
            continue
        seen_phrases.add(key)
        evidence.append({"phrase": phrase, "reason": hit.rule.reason, "rule_id": hit.rule.id})
        if len(evidence) >= MAX_EVIDENCE:
            break
    for combo in combos:
        if len(evidence) >= MAX_EVIDENCE + 1:
            break
        evidence.append({"phrase": "", "reason": combo.reason, "rule_id": combo.id})
    return evidence


def _confidence(level: str, score: float, has_hard: bool, evidence_count: int) -> float:
    """Do tin cay cua *nhan da chon* (khong phai diem rui ro)."""
    if level == LEVEL_DANGEROUS:
        base = 0.75 + 0.2 * min(1.0, (score - THRESHOLD_DANGEROUS) / max(1e-6, 1 - THRESHOLD_DANGEROUS))
        if has_hard:
            base = max(base, 0.9)
        base += 0.01 * min(4, evidence_count)
    elif level == LEVEL_SUSPICIOUS:
        # Vung giua luon kem chac chan hon hai dau.
        mid = (THRESHOLD_DANGEROUS + THRESHOLD_SUSPICIOUS) / 2
        base = 0.72 - 0.25 * abs(score - mid) / max(1e-6, (THRESHOLD_DANGEROUS - THRESHOLD_SUSPICIOUS) / 2)
        base = max(0.55, base)
    else:
        base = 0.7 + 0.29 * (1 - score / max(1e-6, THRESHOLD_SUSPICIOUS))
    return round(max(0.5, min(0.99, base)), 2)


def analyze(
    text: str | None = None,
    pre: PreprocessResult | None = None,
    use_ml: bool = True,
) -> AnalysisResult:
    """Phan loai rui ro cua mot tin nhan.

    Args:
        text: Tin nhan tho. Bo qua neu da truyen ``pre``.
        pre: Ket qua Module 1 (tranh tien xu ly hai lan trong pipeline day du).
        use_ml: Co tron diem cua mo hinh ML hay khong.
    """
    started = time.perf_counter()
    if pre is None:
        if text is None:
            raise ValueError("Can truyen `text` hoac `pre`.")
        pre = preprocess(text)

    hits = _collect_hits(pre)
    # Phan tich ten mien (co danh sach trang chinh thong) chay song song voi bo luat.
    hits += _link_hits_to_rule_hits(analyze_links(pre.original_text))

    matched_ids = {hit.rule.id for hit in hits}
    suppressed: Set[str] = set()
    for trigger, targets in RULE_SUPPRESSIONS.items():
        if trigger in matched_ids:
            suppressed |= targets
    if suppressed:
        hits = [hit for hit in hits if hit.rule.id not in suppressed]

    safe_hits = [h for h in hits if h.rule.signal == SIG_SAFE]
    risk_hits = [h for h in hits if h.rule.signal in RISK_SIGNALS]

    # Luat khuech dai chi co gia tri khi da co tin hieu rui ro that su.
    core_hits = [h for h in risk_hits if not h.rule.amplifier]
    if not core_hits:
        risk_hits = []
    active_signals = {h.rule.signal for h in risk_hits}

    # --- Luat ket hop ---
    combo_hits = [c for c in COMBOS if all(active_signals & group for group in c.requires)]

    rule_score = _noisy_or([h.rule.weight for h in risk_hits] + [c.boost for c in combo_hits])

    # Mot tin hieu don le, yeu va khong thuoc nhom "du suc ket luan" thi khong the
    # tu day len muc nguy hiem (vd: chi nhac toi 1 duong link).
    can_conclude_alone = bool(active_signals & STANDALONE_SIGNALS) or any(
        h.rule.standalone for h in risk_hits
    )
    if not combo_hits and not can_conclude_alone:
        rule_score = min(rule_score, THRESHOLD_DANGEROUS - 0.05)

    has_hard = any(h.rule.hard_danger for h in risk_hits) or any(c.hard_danger for c in combo_hits)

    # --- Tin hieu an toan keo diem xuong (khong ap dung khi da co bang chung chac chan) ---
    safe_score = _noisy_or([h.rule.weight for h in safe_hits])
    if safe_score and not has_hard:
        rule_score *= 1.0 - 0.5 * min(0.6, safe_score)
        # Tin nhan mang ro dang "thong bao dich vu chinh thong" (cu phap tong dai, goi cuoc,
        # thong bao OTP cua chinh ngan hang...) khong duoc phep len muc DO neu khong co
        # bang chung chac chan - nhieu nhat la muc VANG "can chu y".
        if safe_score >= 0.4:
            rule_score = min(rule_score, THRESHOLD_DANGEROUS - 0.02)

    # --- Tron voi cac lop mo hinh (TF-IDF va/hoac PhoBERT) ---
    ml_scores = ml_model.predict_proba(pre.match_text) if use_ml else None
    # PhoBERT doc van ban goc (con dau, con dau cau) vi no hieu ngu canh tieng Viet.
    tr_scores = transformer_model.predict_proba(pre.original_text) if use_ml else None

    def _risk_of(scores: Dict[str, float]) -> float:
        """Quy xac suat 3 lop ve mot diem rui ro duy nhat."""
        return scores.get(LEVEL_DANGEROUS, 0.0) + 0.45 * scores.get(LEVEL_SUSPICIOUS, 0.0)

    components = [(RULE_WEIGHT, rule_score)]
    if ml_scores:
        components.append((ML_WEIGHT, _risk_of(ml_scores)))
    if tr_scores:
        components.append((TRANSFORMER_WEIGHT, _risk_of(tr_scores)))
    total_weight = sum(weight for weight, _ in components)
    final_score = sum(weight * value for weight, value in components) / total_weight

    # Uu tien Recall (Muc 6.1): mo hinh nao rat chac chan thi khong de tin nhan
    # roi ve muc An toan.
    for scores in (ml_scores, tr_scores):
        if not scores:
            continue
        if scores.get(LEVEL_DANGEROUS, 0.0) >= 0.8:
            final_score = max(final_score, THRESHOLD_SUSPICIOUS + 0.05)
        elif scores.get(LEVEL_SUSPICIOUS, 0.0) >= 0.6:
            final_score = max(final_score, THRESHOLD_SUSPICIOUS)

    # Chieu nguoc lai: mo hinh rat chac chan tin nhan an toan thi duoc quyen keo
    # diem xuong - mien la bo luat khong nam giu bang chung chac chan nao.
    if MODEL_SAFE_VETO and not has_hard:
        model_safe = [s.get(LEVEL_SAFE, 0.0) for s in (ml_scores, tr_scores) if s]
        if model_safe and min(model_safe) >= MODEL_SAFE_VETO:
            final_score *= MODEL_SAFE_VETO_FACTOR

    if has_hard:
        final_score = max(final_score, 0.85)
    final_score = round(max(0.0, min(1.0, final_score)), 4)

    if final_score >= THRESHOLD_DANGEROUS:
        level = LEVEL_DANGEROUS
    elif final_score >= THRESHOLD_SUSPICIOUS:
        level = LEVEL_SUSPICIOUS
    else:
        level = LEVEL_SAFE

    category = _pick_category(risk_hits, combo_hits) if level != LEVEL_SAFE else CATEGORY_SAFE
    evidence = _build_evidence(risk_hits, combo_hits, category) if level != LEVEL_SAFE else []
    highlight = [e["phrase"] for e in evidence if e["phrase"]]

    explanation = EXPLANATION_TEMPLATES.get(category, EXPLANATION_TEMPLATES[CATEGORY_SAFE])
    if level != LEVEL_SAFE and category == CATEGORY_SAFE:
        # Mo hinh ML thay giong tin lua dao nhung bo luat chua chi ra tu khoa cu the.
        explanation = (
            "Mô hình AI thấy cách viết của tin nhắn này khá giống các tin nhắn lừa đảo đã gặp, "
            "dù chưa tìm được từ khóa cụ thể. Em hãy cẩn thận và hỏi người lớn trước khi làm theo."
        )
    elif level == LEVEL_SUSPICIOUS and category != CATEGORY_SAFE:
        explanation = (
            "Chưa đủ căn cứ khẳng định là lừa đảo, nhưng tin nhắn có điểm đáng ngờ. " + explanation
        )

    return AnalysisResult(
        risk_level=level,
        risk_score=final_score,
        confidence_score=_confidence(level, final_score, has_hard, len(evidence)),
        scam_category=category,
        evidence=evidence,
        student_explanation=explanation,
        highlight_words=highlight,
        matched_rules=[h.rule.id for h in risk_hits] + [c.id for c in combo_hits],
        signals=sorted(active_signals),
        rule_score=round(rule_score, 4),
        ml_scores={k: round(v, 4) for k, v in ml_scores.items()} if ml_scores else None,
        transformer_scores={k: round(v, 4) for k, v in tr_scores.items()} if tr_scores else None,
        process_time_ms=round((time.perf_counter() - started) * 1000, 2),
    )


# Cau tom tat ngan gon (1 dong) dung cho the ket qua o giao dien.
SUMMARY_TEMPLATES: Dict[str, str] = {
    CATEGORY_GAMBLING: "Tin nhắn dụ nạp tiền vào trang cờ bạc, đổi thưởng trá hình.",
    CATEGORY_IMPERSONATION_TEACHER: "Tin nhắn mạo danh thầy cô/nhà trường để nhờ nạp thẻ hoặc chuyển tiền.",
    CATEGORY_IMPERSONATION_RELATIVE: "Tin nhắn mạo danh người thân, bạn bè để hỏi vay tiền gấp.",
    CATEGORY_GAME_TOPUP: "Tin nhắn dụ nạp thẻ game bằng lời hứa tặng vật phẩm miễn phí.",
    CATEGORY_FAKE_PRIZE: "Tin nhắn báo trúng thưởng giả để đòi phí ứng trước hoặc dụ bấm link.",
    CATEGORY_OTP_PHISHING: "Tin nhắn lừa đảo chiếm đoạt mã OTP/mật khẩu tài khoản của em.",
    CATEGORY_ACCOUNT_THREAT: "Tin nhắn đe dọa, tống tiền hoặc dọa chiếm tài khoản của em.",
    CATEGORY_PHISHING_LINK: "Tin nhắn chứa liên kết lạ dẫn tới trang web giả mạo.",
    CATEGORY_JOB_SCAM: "Lời mời 'việc nhẹ lương cao' nhằm dụ học sinh nộp tiền đặt cọc.",
    CATEGORY_SUSPICIOUS_INVITE: "Lời mời tham gia nhóm/chương trình lạ, chưa rõ mục đích.",
    CATEGORY_ADS_SPAM: "Tin nhắn quảng cáo, chào hàng chưa rõ nguồn gốc.",
    CATEGORY_SAFE: "Không phát hiện dấu hiệu lừa đảo trong tin nhắn này.",
}


def build_summary(analysis: "AnalysisResult") -> str:
    """Cau tom tat 1 dong cho the ket qua (Module 4)."""
    base = SUMMARY_TEMPLATES.get(analysis.scam_category, SUMMARY_TEMPLATES[CATEGORY_SAFE])
    if analysis.risk_level == LEVEL_SUSPICIOUS:
        return "Cần thận trọng: " + base[0].lower() + base[1:]
    return base


def build_badge_title(analysis: "AnalysisResult") -> str:
    """Nhan hien thi tren the ket qua, vi du 'Cực kỳ nguy hiểm - Đánh cắp mã OTP / mật khẩu'."""
    theme = THEME[analysis.risk_level]
    if analysis.risk_level == LEVEL_SAFE or analysis.scam_category == CATEGORY_SAFE:
        return theme["badge_title"]
    prefix = "Cực kỳ nguy hiểm" if analysis.risk_level == LEVEL_DANGEROUS else "Nghi vấn"
    return f"{prefix} - {CATEGORY_TITLES.get(analysis.scam_category, analysis.scam_category)}"
