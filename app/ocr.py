"""Trich xuat van ban tu anh chup man hinh (OCR) - nhanh phu cua Module 1.

OCR la thanh phan *tuy chon*: neu may chu chua cai Tesseract, he thong van hoat
dong binh thuong voi luong nhap van ban, va API se tra loi bao loi ro rang
thay vi bao loi chung chung.
"""

from __future__ import annotations

import io
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class OCRUnavailableError(RuntimeError):
    """Khong co thu vien/cong cu OCR tren may chu."""


class OCRFailedError(RuntimeError):
    """Doc duoc anh nhung khong trich xuat duoc chu."""


def is_available() -> Tuple[bool, str]:
    """Kiem tra OCR co san sang khong, kem thong diep giai thich."""
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        return False, f"Thiếu thư viện Python cho OCR ({exc.name}). Cài: pip install pillow pytesseract"
    try:
        import pytesseract

        version = pytesseract.get_tesseract_version()
    except Exception as exc:  # pragma: no cover - phu thuoc moi truong
        return False, (
            "Chưa cài công cụ Tesseract OCR trên hệ thống "
            f"(sudo apt-get install tesseract-ocr tesseract-ocr-vie). Chi tiết: {exc}"
        )
    return True, f"Tesseract {version}"


def extract_text(image_bytes: bytes, lang: str = "vie+eng") -> str:
    """Doc chu tu anh chup man hinh tin nhan."""
    available, message = is_available()
    if not available:
        raise OCRUnavailableError(message)

    import pytesseract
    from PIL import Image

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L")  # anh xam giup OCR on dinh hon voi anh chup man hinh
    except Exception as exc:
        raise OCRFailedError(f"Không mở được tệp ảnh: {exc}") from exc

    try:
        text = pytesseract.image_to_string(image, lang=lang)
    except Exception:
        # Thieu goi ngon ngu tieng Viet -> thu lai voi tieng Anh de khong chet han.
        logger.warning("OCR tiếng Việt thất bại, thử lại với gói ngôn ngữ mặc định.")
        try:
            text = pytesseract.image_to_string(image)
        except Exception as exc:  # pragma: no cover
            raise OCRFailedError(f"OCR thất bại: {exc}") from exc

    text = text.strip()
    if not text:
        raise OCRFailedError("Không đọc được chữ nào trong ảnh. Em thử chụp rõ hơn hoặc dán văn bản nhé!")
    return text
