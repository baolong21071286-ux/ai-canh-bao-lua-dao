"""Lop mo hinh Transformer ma nguon mo (mac dinh: PhoBERT) - tuy chon.

Vi sao them?
    Bo luat giai thich duoc nhung khong phu het cach dien dat; TF-IDF bat duoc tu
    ngu nhung khong hieu ngu canh. Mot mo hinh ngon ngu tieng Viet da huan luyen
    san (PhoBERT cua VinAI, giay phep MIT) hieu ngu canh tot hon han va la cach
    nang chat luong ro ret nhat ma van chay duoc tren may thuong (CPU).

Thiet ke:
    * Hoan toan **tuy chon**: thieu `torch`/`transformers` hoac chua huan luyen
      thi he thong chay binh thuong voi bo luat + TF-IDF.
    * Nap mo hinh mot lan roi giu trong bo nho (lazy singleton).
    * Chay tren CPU, do dai toi da 128 token - du cho tin nhan SMS.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from app.config import LEVEL_BY_LABEL, MODEL_DIR

logger = logging.getLogger(__name__)

#: Mo hinh nen mac dinh. Co the doi bang bien moi truong SCAM_TRANSFORMER_BASE.
DEFAULT_BASE_MODEL = os.getenv("SCAM_TRANSFORMER_BASE", "vinai/phobert-base-v2")
#: Thu muc chua mo hinh da tinh chinh (fine-tuned).
TRANSFORMER_DIR = Path(os.getenv("SCAM_TRANSFORMER_PATH", MODEL_DIR / "phobert_scam"))
MAX_LENGTH = 128

_bundle = None
_load_attempted = False


class _Bundle:
    def __init__(self, tokenizer, model, labels: List[int]):
        self.tokenizer = tokenizer
        self.model = model
        self.labels = labels


def is_available() -> bool:
    return load() is not None


def load(path: Path = TRANSFORMER_DIR, force: bool = False):
    """Nap mo hinh da tinh chinh; tra ve ``None`` neu khong co (khong phai loi)."""
    global _bundle, _load_attempted
    if _load_attempted and not force:
        return _bundle
    _load_attempted = True
    _bundle = None

    path = Path(path)
    if not (path / "config.json").exists():
        logger.info("Chua co mo hinh Transformer tai %s - bo qua lop nay.", path)
        return None
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        logger.info("Chua cai torch/transformers - bo qua lop Transformer.")
        return None

    try:
        tokenizer = AutoTokenizer.from_pretrained(str(path))
        model = AutoModelForSequenceClassification.from_pretrained(str(path))
        model.eval()
        torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))
        meta_path = path / "label_map.json"
        labels = json.loads(meta_path.read_text())["labels"] if meta_path.exists() else [0, 1, 2]
        _bundle = _Bundle(tokenizer, model, labels)
        logger.info("Da nap mo hinh Transformer tu %s", path)
    except Exception as exc:  # pragma: no cover - phu thuoc moi truong
        logger.warning("Khong nap duoc mo hinh Transformer (%s).", exc)
        _bundle = None
    return _bundle


def predict_proba(text: str) -> Optional[Dict[str, float]]:
    """Xac suat theo tung muc rui ro, hoac ``None`` neu khong co mo hinh."""
    bundle = load()
    if bundle is None:
        return None
    try:
        import torch

        encoded = bundle.tokenizer(
            text, truncation=True, max_length=MAX_LENGTH, return_tensors="pt"
        )
        with torch.no_grad():
            logits = bundle.model(**encoded).logits[0]
            probs = torch.softmax(logits, dim=-1).tolist()
    except Exception as exc:  # pragma: no cover
        logger.warning("Loi suy luan Transformer: %s", exc)
        return None
    return {LEVEL_BY_LABEL[label]: float(p) for label, p in zip(bundle.labels, probs)}
