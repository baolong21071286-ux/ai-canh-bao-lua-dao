"""Hang so cau hinh dung chung: nguong rui ro, ma mau, danh muc lua dao."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
FRONTEND_DIR = BASE_DIR / "frontend"

DATASET_FULL = DATA_DIR / "dataset_thcs_scam.jsonl"
DATASET_DEMO = DATA_DIR / "dataset_demo_60.jsonl"
MODEL_PATH = Path(os.getenv("SCAM_MODEL_PATH", MODEL_DIR / "scam_clf.joblib"))

API_TITLE = "AI Canh bao Tin nhan Lua dao cho hoc sinh THCS"
API_VERSION = "1.0.0"

# --- Thang 3 muc rui ro (Muc 1.2 & 2 cua dac ta) ---
LEVEL_SAFE = "SAFE"
LEVEL_SUSPICIOUS = "SUSPICIOUS"
LEVEL_DANGEROUS = "DANGEROUS"

LEVEL_BY_LABEL = {0: LEVEL_SAFE, 1: LEVEL_SUSPICIOUS, 2: LEVEL_DANGEROUS}
LABEL_BY_LEVEL = {v: k for k, v in LEVEL_BY_LABEL.items()}

# Ma mau lay dung theo Muc 5.1 cua dac ta ky thuat.
THEME = {
    LEVEL_SAFE: {
        "color_name": "GREEN",
        "hex": "#38A169",
        "emoji": "🟢",
        "badge_title": "An toàn - Tin nhắn bình thường",
        "headline": "Tin nhắn bình thường, bạn có thể yên tâm!",
    },
    LEVEL_SUSPICIOUS: {
        "color_name": "YELLOW",
        "hex": "#D69E2E",
        "emoji": "🟡",
        "badge_title": "Nghi vấn - Cần chú ý",
        "headline": "Có dấu hiệu lạ, hãy cẩn thận suy nghĩ!",
    },
    LEVEL_DANGEROUS: {
        "color_name": "RED",
        "hex": "#E53E3E",
        "emoji": "🔴",
        "badge_title": "Cực kỳ nguy hiểm - Dấu hiệu lừa đảo",
        "headline": "Cảnh báo lừa đảo! Hãy dừng lại ngay!",
    },
}

# --- Nguong quyet dinh nhan tu diem rui ro [0, 1] ---
# Nguong DANGEROUS duoc ha thap co chu dich: dac ta yeu cau Recall >= 95% tren
# nhan nguy hiem (Muc 6.1), tuc la "tha nham con hon bo sot".
THRESHOLD_DANGEROUS = 0.58
THRESHOLD_SUSPICIOUS = 0.26

# Trong so tron giua cac lop. Lop nao khong co thi trong so duoc chia lai cho cac
# lop con lai, nen he thong chay duoc voi bat ky to hop nao:
#   - chi bo luat                (mac dinh khi moi tai kho ma nguon ve)
#   - bo luat + TF-IDF           (sau khi chay scripts/train_model.py)
#   - bo luat + TF-IDF + PhoBERT (sau khi chay scripts/train_transformer.py)
RULE_WEIGHT = 0.65
ML_WEIGHT = 0.35
TRANSFORMER_WEIGHT = 0.5

# Khi mo hinh hoc may RAT CHAC CHAN tin nhan la an toan (>= nguong nay) va bo luat
# khong co bang chung chac chan nao, diem rui ro bi keo xuong. Co che nay can thiet
# vi bo luat duoc viet cho ngu canh hoc duong: mang sang mien tin nhan khac (SMS
# ngan hang, khuyen mai cua nha mang) no bao dong nham rat nhieu.
# Dat 0 de tat co che nay.
MODEL_SAFE_VETO = 0.8
MODEL_SAFE_VETO_FACTOR = 0.4

# Gioi han dau vao (Muc 3, Module 1)
MAX_TEXT_LENGTH = 2000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg"}

# --- Danh muc kich ban lua dao ---
CATEGORY_SAFE = "SAFE"
CATEGORY_IMPERSONATION_TEACHER = "IMPERSONATION_TEACHER"
CATEGORY_IMPERSONATION_RELATIVE = "IMPERSONATION_RELATIVE"
CATEGORY_GAME_TOPUP = "GAME_TOPUP_SCAM"
CATEGORY_FAKE_PRIZE = "FAKE_PRIZE"
CATEGORY_OTP_PHISHING = "OTP_PHISHING"
CATEGORY_ACCOUNT_THREAT = "ACCOUNT_THREAT"
CATEGORY_PHISHING_LINK = "PHISHING_LINK"
CATEGORY_JOB_SCAM = "JOB_SCAM"
CATEGORY_GAMBLING = "GAMBLING_SCAM"
CATEGORY_SUSPICIOUS_INVITE = "SUSPICIOUS_INVITE"
CATEGORY_ADS_SPAM = "ADS_SPAM"

CATEGORY_TITLES = {
    CATEGORY_SAFE: "Tin nhắn sinh hoạt/học tập bình thường",
    CATEGORY_IMPERSONATION_TEACHER: "Mạo danh thầy cô, nhà trường",
    CATEGORY_IMPERSONATION_RELATIVE: "Mạo danh bạn bè, người thân",
    CATEGORY_GAME_TOPUP: "Bẫy nạp thẻ game, tặng vật phẩm miễn phí",
    CATEGORY_FAKE_PRIZE: "Thông báo trúng thưởng giả",
    CATEGORY_OTP_PHISHING: "Đánh cắp mã OTP / mật khẩu",
    CATEGORY_ACCOUNT_THREAT: "Đe dọa, tống tiền, chiếm tài khoản",
    CATEGORY_PHISHING_LINK: "Liên kết lạ dẫn tới trang giả mạo",
    CATEGORY_JOB_SCAM: "Dụ việc nhẹ lương cao",
    CATEGORY_GAMBLING: "Dụ nạp tiền cờ bạc, đổi thưởng",
    CATEGORY_SUSPICIOUS_INVITE: "Lời mời vào nhóm lạ",
    CATEGORY_ADS_SPAM: "Quảng cáo, spam chưa rõ nguồn gốc",
}

# Do uu tien khi nhieu kich ban cung duoc kich hoat (so lon = uu tien hon).
CATEGORY_PRIORITY = {
    CATEGORY_OTP_PHISHING: 100,
    CATEGORY_ACCOUNT_THREAT: 95,
    CATEGORY_IMPERSONATION_TEACHER: 90,
    CATEGORY_IMPERSONATION_RELATIVE: 85,
    CATEGORY_GAME_TOPUP: 80,
    CATEGORY_FAKE_PRIZE: 75,
    CATEGORY_JOB_SCAM: 70,
    CATEGORY_GAMBLING: 72,
    CATEGORY_PHISHING_LINK: 65,
    CATEGORY_SUSPICIOUS_INVITE: 40,
    CATEGORY_ADS_SPAM: 30,
    CATEGORY_SAFE: 0,
}
