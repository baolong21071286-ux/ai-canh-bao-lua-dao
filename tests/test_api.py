"""Kiem thu tang REST API (Module 1-4) theo dung dac ta ky thuat."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SCAM_MESSAGE = "Nhập mã OTP vừa gửi về điện thoại để nhận 1000 Robux miễn phí tại web robux-thcs.vip"
SAFE_MESSAGE = "Mai nhớ mang vở bài tập Toán nhé, cô kiểm tra 15 phút đấy!"


def test_health():
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok"
    assert body["rules_loaded"] > 0


def test_preprocess_json():
    response = client.post(
        "/api/v1/scan/preprocess",
        json={"input_mode": "raw_text", "raw_text": "nap ho thay 2 the viettel 100k vao so 0987654321 gap"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) >= {"cleaned_text", "normalized_text", "extracted_entities", "metadata"}
    assert "0987654321" in data["extracted_entities"]["phone_numbers"]
    assert data["metadata"]["process_time_ms"] >= 0


def test_preprocess_rejects_empty_text():
    response = client.post("/api/v1/scan/preprocess", json={"input_mode": "raw_text", "raw_text": "   "})
    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_preprocess_screenshot_requires_multipart():
    response = client.post("/api/v1/scan/preprocess", json={"input_mode": "screenshot"})
    assert response.status_code == 400


def test_preprocess_rejects_non_image_upload():
    response = client.post(
        "/api/v1/scan/preprocess",
        files={"image_file": ("note.txt", b"khong phai anh", "text/plain")},
        data={"input_mode": "screenshot"},
    )
    assert response.status_code == 415


def test_analyze_endpoint_matches_spec_schema():
    response = client.post("/api/v1/scan/analyze", json={"normalized_text": SCAM_MESSAGE})
    assert response.status_code == 200
    analysis = response.json()["analysis"]
    assert analysis["risk_level"] == "DANGEROUS"
    assert analysis["risk_color"] == "RED"
    assert analysis["trigger_evidence"]
    assert analysis["student_explanation"]
    for item in analysis["trigger_evidence"]:
        assert "reason" in item and "phrase" in item


def test_analyze_rejects_too_long_text():
    response = client.post("/api/v1/scan/analyze", json={"normalized_text": "a" * 2001})
    assert response.status_code == 422


def test_educate_endpoint():
    response = client.post(
        "/api/v1/scan/educate",
        json={"risk_level": "DANGEROUS", "scam_category": "IMPERSONATION_TEACHER", "highlight_words": ["nạp hộ"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action_plan"]["steps"]
    assert body["micro_learning"]["quiz"]["correct_option"]


def test_educate_rejects_invalid_level():
    response = client.post("/api/v1/scan/educate", json={"risk_level": "TIM", "scam_category": "SAFE"})
    assert response.status_code == 400


def test_quick_check_dangerous():
    response = client.post("/api/v1/scan/quick-check", json={"content": SCAM_MESSAGE, "channel": "Discord"})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    result = body["result"]
    assert result["verdict"]["level"] == "DANGEROUS"
    assert result["verdict"]["theme_color"] == "#E53E3E"
    assert result["highlight_words"]
    assert result["immediate_actions"]
    assert result["interactive_quiz"]["correct"] in {"A", "B", "C"}
    # Dac ta Muc 6.1: do tre xu ly < 1000ms
    assert result["meta"]["process_time_ms"] < 1000


def test_quick_check_safe_message_has_no_highlight():
    result = client.post("/api/v1/scan/quick-check", json={"content": SAFE_MESSAGE}).json()["result"]
    assert result["verdict"]["level"] == "SAFE"
    assert result["verdict"]["theme_color"] == "#38A169"
    assert result["highlight_words"] == []


def test_quick_check_with_details_exposes_all_modules():
    result = client.post(
        "/api/v1/scan/quick-check", json={"content": SCAM_MESSAGE, "include_details": True}
    ).json()["result"]
    assert set(result["details"]) == {"module_1_preprocess", "module_2_analysis", "module_3_education"}


def test_quick_check_requires_content():
    assert client.post("/api/v1/scan/quick-check", json={}).status_code == 422


def test_learning_endpoints():
    cards = client.get("/api/v1/learn/flashcards").json()
    quizzes = client.get("/api/v1/learn/quizzes").json()
    assert cards["total"] == len(cards["flashcards"]) > 0
    assert quizzes["total"] == len(quizzes["quizzes"]) > 0


def test_quiz_check_endpoint():
    response = client.post("/api/v1/learn/quiz/check", json={"quiz_id": "QZ_IMP_01", "option_id": "C"})
    assert response.json()["result"]["is_correct"] is True
    missing = client.post("/api/v1/learn/quiz/check", json={"quiz_id": "XX", "option_id": "A"})
    assert missing.status_code == 404


def test_meta_categories():
    body = client.get("/api/v1/meta/categories").json()
    assert "DANGEROUS" in body["risk_levels"]
    assert "OTP_PHISHING" in body["scam_categories"]


def test_frontend_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Kiểm tra ngay" in response.text
