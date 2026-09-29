"""GIAI DOAN 3 - REST API bang FastAPI cho he thong canh bao tin nhan lua dao.

Cac nhom endpoint:
    * ``/api/v1/scan/*``  : 4 module theo dac ta (preprocess, analyze, educate, quick-check).
    * ``/api/v1/learn/*`` : tra cuu flashcard / mini-quiz va cham diem cau tra loi.
    * ``/api/v1/meta/*``  : thong tin he thong (danh muc kich ban, trang thai mo hinh).

Chay thu::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import ml_model, ocr, transformer_model
from app.classifier import AnalysisResult, analyze
from app.config import (
    ALLOWED_IMAGE_TYPES,
    API_TITLE,
    API_VERSION,
    CATEGORY_TITLES,
    FRONTEND_DIR,
    LEVEL_SAFE,
    MAX_IMAGE_BYTES,
    MAX_TEXT_LENGTH,
    THEME,
)
from app.education import build_education, check_answer, list_flashcards, list_quizzes
from app.engine_export import build_engine_data
from app.pipeline import quick_check
from app.preprocessor import PreprocessError, preprocess, rebuild_from_normalized
from app.rules import ALL_RULES
from app.schemas import (
    AnalyzeRequest,
    EducateRequest,
    QuickCheckRequest,
    QuizAnswerRequest,
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Nap san mo hinh khi khoi dong.

    Neu de nap lazy, hoc sinh bam "Kiem tra ngay" lan dau se phai cho vai giay
    (PhoBERT nap mat ~4s). Nap truoc o day thi moi request deu nhanh.
    """
    if ml_model.is_available():
        logger.info("Đã nạp mô hình TF-IDF.")
    if transformer_model.is_available():
        logger.info("Đã nạp mô hình PhoBERT.")
    yield


app = FastAPI(
    lifespan=lifespan,
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Hệ thống AI nhận diện và cảnh báo tin nhắn có dấu hiệu lừa đảo, "
        "kèm lời khuyên xử lý và mini-quiz nâng cao kỹ năng an toàn số cho học sinh THCS."
    ),
)

# Cho phep giao dien web/tien ich Chrome goi truc tiep tu trinh duyet.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PreprocessError)
async def preprocess_error_handler(_: Request, exc: PreprocessError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"status": "error", "code": 400, "message": str(exc)})


# ---------------------------------------------------------------------------
# MODULE 1 - Ingestion & Preprocessing
# ---------------------------------------------------------------------------
@app.post("/api/v1/scan/preprocess", tags=["Module 1 - Tiền xử lý"])
async def api_preprocess(request: Request) -> Dict[str, Any]:
    """Lam sach tin nhan va trich xuat thuc the.

    Ho tro ca ``application/json`` (raw_text) va ``multipart/form-data`` (anh chup man hinh).
    """
    content_type = (request.headers.get("content-type") or "").lower()
    input_mode = "raw_text"
    raw_text = ""

    if "multipart/form-data" in content_type:
        form = await request.form()
        input_mode = str(form.get("input_mode") or "screenshot")
        upload = form.get("image_file")
        if input_mode == "screenshot" or upload is not None:
            if upload is None:
                raise HTTPException(status_code=400, detail="Thiếu tệp ảnh `image_file`.")
            if upload.content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=415,
                    detail=f"Chỉ hỗ trợ ảnh PNG/JPG. Tệp gửi lên có kiểu: {upload.content_type}",
                )
            image_bytes = await upload.read()
            if len(image_bytes) > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=413, detail="Ảnh vượt quá giới hạn 5MB.")
            try:
                raw_text = ocr.extract_text(image_bytes)
            except ocr.OCRUnavailableError as exc:
                raise HTTPException(status_code=503, detail=f"Máy chủ chưa bật OCR. {exc}") from exc
            except ocr.OCRFailedError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            input_mode = "screenshot"
        else:
            raw_text = str(form.get("raw_text") or "")
    else:
        body = await request.json()
        input_mode = str(body.get("input_mode") or "raw_text")
        raw_text = str(body.get("raw_text") or "")
        if input_mode == "screenshot":
            raise HTTPException(
                status_code=400,
                detail="Chế độ `screenshot` cần gửi tệp ảnh qua multipart/form-data.",
            )

    result = preprocess(raw_text, source_type=input_mode)
    return {"status": "success", "data": result.to_dict()}


# ---------------------------------------------------------------------------
# MODULE 2 - Phan loai & giai thich
# ---------------------------------------------------------------------------
@app.post("/api/v1/scan/analyze", tags=["Module 2 - Phân loại & Giải thích"])
async def api_analyze(payload: AnalyzeRequest) -> Dict[str, Any]:
    """Phan loai rui ro 3 muc va tra ve bang chung giai thich duoc."""
    pre = rebuild_from_normalized(payload.normalized_text, payload.extracted_entities)
    analysis = analyze(pre=pre)
    return {"status": "success", "analysis": analysis.to_dict()}


# ---------------------------------------------------------------------------
# MODULE 3 - Hanh dong khuyen nghi & hoc tap
# ---------------------------------------------------------------------------
@app.post("/api/v1/scan/educate", tags=["Module 3 - Hành động & Giáo dục"])
async def api_educate(payload: EducateRequest) -> Dict[str, Any]:
    """Sinh ke hoach hanh dong + flashcard + mini-quiz tu ket qua cua Module 2."""
    if payload.risk_level not in THEME:
        raise HTTPException(
            status_code=400,
            detail=f"`risk_level` phải thuộc {sorted(THEME)}; nhận được: {payload.risk_level}",
        )
    analysis = AnalysisResult(
        risk_level=payload.risk_level,
        risk_score=0.0,
        confidence_score=payload.confidence_score,
        scam_category=payload.scam_category,
        evidence=payload.trigger_evidence,
        student_explanation=payload.student_explanation,
        highlight_words=payload.highlight_words,
        matched_rules=[],
        signals=[],
        rule_score=0.0,
        ml_scores=None,
        process_time_ms=0.0,
    )
    return build_education(analysis, seed=" ".join(payload.highlight_words) or payload.scam_category)


# ---------------------------------------------------------------------------
# MODULE 4 - Unified Client API
# ---------------------------------------------------------------------------
@app.post("/api/v1/scan/quick-check", tags=["Module 4 - API hợp nhất"])
async def api_quick_check(payload: QuickCheckRequest) -> Dict[str, Any]:
    """Mot request duy nhat -> day du du lieu hien thi cho giao dien hoc sinh."""
    result = quick_check(
        payload.content,
        channel=payload.channel,
        include_details=payload.include_details,
    )
    return {"code": 200, "result": result}


# ---------------------------------------------------------------------------
# Hoc tap: flashcard & mini-quiz
# ---------------------------------------------------------------------------
@app.get("/api/v1/learn/flashcards", tags=["Học tập"])
async def api_flashcards() -> Dict[str, Any]:
    cards = list_flashcards()
    return {"status": "success", "total": len(cards), "flashcards": cards}


@app.get("/api/v1/learn/quizzes", tags=["Học tập"])
async def api_quizzes() -> Dict[str, Any]:
    quizzes = list_quizzes()
    return {"status": "success", "total": len(quizzes), "quizzes": quizzes}


@app.post("/api/v1/learn/quiz/check", tags=["Học tập"])
async def api_quiz_check(payload: QuizAnswerRequest) -> Dict[str, Any]:
    """Cham diem cau tra loi mini-quiz cua hoc sinh."""
    try:
        return {"status": "success", "result": check_answer(payload.quiz_id, payload.option_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy quiz `{payload.quiz_id}`.") from exc


# ---------------------------------------------------------------------------
# Thong tin he thong
# ---------------------------------------------------------------------------
@app.get("/api/v1/health", tags=["Hệ thống"])
async def api_health() -> Dict[str, Any]:
    ocr_ready, ocr_message = ocr.is_available()
    return {
        "status": "ok",
        "version": API_VERSION,
        "rules_loaded": len(ALL_RULES),
        "ml_model_loaded": ml_model.is_available(),
        "transformer_loaded": transformer_model.is_available(),
        "ocr_available": ocr_ready,
        "ocr_detail": ocr_message,
        "max_text_length": MAX_TEXT_LENGTH,
    }


@app.get("/api/v1/meta/categories", tags=["Hệ thống"])
async def api_categories() -> Dict[str, Any]:
    return {
        "status": "success",
        "risk_levels": THEME,
        "scam_categories": CATEGORY_TITLES,
    }


# ---------------------------------------------------------------------------
# Giao dien demo (Giai doan 4)
# ---------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/engine.js", include_in_schema=False)
    async def engine_js() -> FileResponse:
        """Bo may chay trong trinh duyet (dung khi mat ket noi toi may chu)."""
        return FileResponse(str(FRONTEND_DIR / "engine.js"), media_type="application/javascript")

    @app.get("/engine-data.json", include_in_schema=False)
    async def engine_data() -> Dict[str, Any]:
        """Toan bo luat + noi dung giao duc duoi dang JSON cho ban chay offline."""
        return build_engine_data()
