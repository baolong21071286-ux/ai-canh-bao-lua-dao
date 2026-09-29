"""Lop mo hinh hoc may (TF-IDF + Linear Classifier) bo tro cho bo luat.

Vai tro trong he thong:
    - Bo luat (rules) chiu trach nhiem **giai thich duoc** va bat cac mau lua dao da biet.
    - Mo hinh ML bat cac cach dien dat moi/la ma bo luat chua phu.
    - Hai nguon duoc tron theo trong so RULE_WEIGHT / ML_WEIGHT trong `app.config`.

Neu chua huan luyen mo hinh (hoac thieu scikit-learn) he thong van chay binh thuong
voi 100% suc manh tu bo luat.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.config import LEVEL_BY_LABEL, MODEL_PATH
from app.text_utils import deleet, fold

logger = logging.getLogger(__name__)

_model = None
_model_loaded = False


def build_pipeline():
    """Tao pipeline TF-IDF (word 1-2 gram + char 3-5 gram) -> LogisticRegression."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline, FeatureUnion

    features = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        ]
    )
    return Pipeline(
        [
            ("features", features),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    C=4.0,
                    # Uu tien Recall cho nhan nguy hiem theo Muc 6.1 cua dac ta.
                    class_weight={0: 1.0, 1: 1.2, 2: 1.6},
                ),
            ),
        ]
    )


def normalize_for_model(text: str) -> str:
    """Chuan hoa dau vao cho mo hinh: giong het chuan hoa cua bo luat."""
    return deleet(fold(text))


def train(texts: Sequence[str], labels: Sequence[int]):
    """Huan luyen pipeline tren tap (text, label 0/1/2)."""
    pipeline = build_pipeline()
    pipeline.fit([normalize_for_model(t) for t in texts], list(labels))
    return pipeline


def save(pipeline, path: Path = MODEL_PATH) -> Path:
    import joblib

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)
    return path


def load(path: Path = MODEL_PATH, force: bool = False):
    """Nap mo hinh da luu (chi nap 1 lan, cache lai). Tra ve ``None`` neu khong co."""
    global _model, _model_loaded
    if _model_loaded and not force:
        return _model
    _model_loaded = True
    _model = None
    if not Path(path).exists():
        logger.info("Chua co mo hinh ML tai %s - he thong chay bang bo luat.", path)
        return None
    try:
        import joblib

        _model = joblib.load(path)
        logger.info("Da nap mo hinh ML tu %s", path)
    except Exception as exc:  # pragma: no cover - phu thuoc moi truong
        logger.warning("Khong nap duoc mo hinh ML (%s). Dung bo luat thay the.", exc)
        _model = None
    return _model


def is_available() -> bool:
    return load() is not None


def predict_proba(text: str) -> Optional[Dict[str, float]]:
    """Tra ve xac suat theo tung muc rui ro, hoac ``None`` neu khong co mo hinh."""
    model = load()
    if model is None:
        return None
    try:
        proba = model.predict_proba([normalize_for_model(text)])[0]
        classes = list(model.classes_)
    except Exception as exc:  # pragma: no cover
        logger.warning("Loi khi suy luan mo hinh ML: %s", exc)
        return None
    return {LEVEL_BY_LABEL[int(cls)]: float(p) for cls, p in zip(classes, proba)}
