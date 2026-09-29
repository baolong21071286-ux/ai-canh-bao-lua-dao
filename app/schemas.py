"""Schema Pydantic cho cac endpoint (dung sinh tai lieu OpenAPI tu dong)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.config import MAX_TEXT_LENGTH


class PreprocessJSONRequest(BaseModel):
    """Dau vao Module 1 khi gui bang JSON."""

    input_mode: str = Field("raw_text", description='"raw_text" hoac "screenshot"')
    raw_text: Optional[str] = Field(
        None, description=f"Noi dung tin nhan (toi da {MAX_TEXT_LENGTH} ky tu)", max_length=MAX_TEXT_LENGTH
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "input_mode": "raw_text",
                "raw_text": "thay Nam the duc day, nap ho thay 2 the viettel 100k vao so nay gap",
            }
        }
    }


class AnalyzeRequest(BaseModel):
    """Dau vao Module 2 (nhan ket qua cua Module 1)."""

    normalized_text: str = Field(..., max_length=MAX_TEXT_LENGTH)
    extracted_entities: Optional[Dict[str, List[str]]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "normalized_text": "thầy nam thể dục đây , nạp hộ thầy 2 thẻ viettel 100k vào số này gấp .",
                "extracted_entities": {
                    "urls": [],
                    "phone_numbers": ["0987654321"],
                    "financial_keywords": ["nạp hộ", "thẻ viettel 100k"],
                    "urgency_markers": ["gấp"],
                },
            }
        }
    }


class EducateRequest(BaseModel):
    """Dau vao Module 3: doi tuong `analysis` tra ve tu Module 2."""

    risk_level: str = Field(..., description="SAFE | SUSPICIOUS | DANGEROUS")
    scam_category: str = Field("SAFE")
    confidence_score: float = 0.0
    highlight_words: List[str] = Field(default_factory=list)
    trigger_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    student_explanation: str = ""


class QuickCheckRequest(BaseModel):
    """Dau vao Module 4 - endpoint chinh cho giao dien nguoi dung."""

    content: str = Field(..., max_length=MAX_TEXT_LENGTH, description="Noi dung tin nhan can kiem tra")
    channel: Optional[str] = Field(None, description="Kenh nhan tin: Zalo, Messenger, Discord, SMS...")
    include_details: bool = Field(False, description="Tra ve them du lieu tho cua tung module")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Nhập mã OTP vừa gửi về điện thoại để nhận 1000 Robux miễn phí tại web robux-thcs.vip",
                "channel": "Discord",
            }
        }
    }


class QuizAnswerRequest(BaseModel):
    """Hoc sinh chon dap an cho mini-quiz."""

    quiz_id: str
    option_id: str = Field(..., description="A, B hoac C")


class ErrorResponse(BaseModel):
    status: str = "error"
    code: int = 400
    message: str
