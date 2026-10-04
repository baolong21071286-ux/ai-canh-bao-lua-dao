"""Xuat cac lop mo hinh hoc may sang dang trinh duyet doc duoc (ban demo GitHub Pages).

* TF-IDF + LogisticRegression  -> ``tfidf-model.json`` (tu vung, IDF, he so) - ``frontend/models.js``
  tinh lai dung cong thuc cua scikit-learn nen ket qua khop voi ban Python.
* PhoBERT -> ``phobert/model.onnx.partNN`` (trong so nen int8, tinh bang fp32) + ``phobert/tokenizer.json``
  (tu vung + bang ghep BPE) - chay bang onnxruntime-web.

Ca hai deu la tuy chon: thieu mo hinh nao thi ban web chi bo qua lop do.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

#: So chu so co nghia khi lam tron trong so (giam kich thuoc JSON, sai so ~1e-5).
_PRECISION = 6


def _round(values) -> List[float]:
    return [float(f"{float(v):.{_PRECISION}g}") for v in values]


def export_tfidf(pipeline) -> Dict:
    """Dong goi pipeline FeatureUnion(TfidfVectorizer...) -> LogisticRegression thanh dict."""
    features = pipeline.named_steps["features"]
    clf = pipeline.named_steps["clf"]
    vectorizers = []
    offset = 0
    for name, vec in features.transformer_list:
        unsupported = (
            not vec.lowercase
            or vec.strip_accents
            or vec.preprocessor
            or vec.tokenizer
            or vec.stop_words
            or vec.token_pattern != r"(?u)\b\w\w+\b"
            or vec.analyzer not in ("word", "char_wb")
            or vec.norm != "l2"
            or not vec.use_idf
        )
        if unsupported:
            raise ValueError(f"Bo vector hoa '{name}' dung tuy chon ma ban JS chua ho tro.")
        terms = [""] * len(vec.vocabulary_)
        for term, index in vec.vocabulary_.items():
            terms[index] = term
        vectorizers.append(
            {
                "name": name,
                "analyzer": vec.analyzer,
                "ngramRange": list(vec.ngram_range),
                "sublinearTf": bool(vec.sublinear_tf),
                "offset": offset,
                "terms": terms,
                "idf": _round(vec.idf_),
            }
        )
        offset += len(terms)
    return {
        "type": "tfidf-logreg",
        "classes": [int(c) for c in clf.classes_],
        "intercept": _round(clf.intercept_),
        "coef": [_round(row) for row in clf.coef_],
        "vectorizers": vectorizers,
    }


def write_tfidf(out_path: Path, model_path: Optional[Path] = None) -> Optional[Path]:
    """Ghi ``tfidf-model.json``; tra ve ``None`` neu chua huan luyen mo hinh."""
    from app import ml_model
    from app.config import MODEL_PATH

    pipeline = ml_model.load(model_path or MODEL_PATH, force=True)
    if pipeline is None:
        return None
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(export_tfidf(pipeline), ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    return out_path


#: Kich thuoc toi da moi manh tep mo hinh tren GitHub Pages (tranh tep qua lon).
CHUNK_BYTES = 40 * 1024 * 1024


def export_phobert_tokenizer(tokenizer, labels: List[int], max_length: int) -> Dict:
    """Tu vung + bang ghep BPE (theo thu tu uu tien) cua ``PhobertTokenizer``."""
    # Vai dong cua bpe.codes khong phai mot cap (khong bao gio khop) -> bo qua; chi
    # thu tu tuong doi giua cac cap la quan trong.
    merges = sorted(
        ((pair, rank) for pair, rank in tokenizer.bpe_ranks.items() if len(pair) == 2),
        key=lambda item: item[1],
    )
    return {
        "type": "phobert-bpe",
        "vocab": tokenizer.get_vocab(),
        "merges": [f"{a} {b}" for (a, b), _ in merges],
        "bosId": tokenizer.bos_token_id,
        "eosId": tokenizer.eos_token_id,
        "unkId": tokenizer.unk_token_id,
        "maxLength": max_length,
        "labels": labels,
    }


def quantize_weights_int8(src: Path, dst: Path, min_size: int = 100_000) -> None:
    """Nen *trong so* MatMul/Gather xuong int8 theo tung kenh, nhung van TINH bang fp32.

    Vi sao khong dung ``quantize_dynamic`` cua onnxruntime? Cach do luong tu hoa ca
    activation luc chay, do tren tap test 597 tin that: 2-3% tin bi doi nhan so voi
    PyTorch va Recall tin nguy hiem giam tu 0.943 xuong 0.918. Chi nen trong so
    (DequantizeLinear -> fp32) cho kich thuoc gan nhu nhau (~138 MB) ma khop nhan 100%.
    """
    import numpy as np
    import onnx
    from onnx import helper, numpy_helper

    model = onnx.load(str(src))
    graph = model.graph
    initializers = {init.name: init for init in graph.initializer}
    # MatMul: W[K, N] -> moi kenh ra (cot) mot he so; Gather (bang embedding): moi tu (hang) mot he so.
    targets: Dict[str, int] = {}
    for node in graph.node:
        if node.op_type == "MatMul" and node.input[1] in initializers:
            targets[node.input[1]] = 1
        elif node.op_type == "Gather" and node.input[0] in initializers:
            targets[node.input[0]] = 0

    dequant_nodes = []
    for name, axis in targets.items():
        weight = numpy_helper.to_array(initializers[name]).astype(np.float32)
        if weight.ndim != 2 or weight.size < min_size:
            continue
        amax = np.abs(weight).max(axis=1 - axis)
        scale = np.where(amax > 0, amax / 127.0, 1.0).astype(np.float32)
        shape = (1, -1) if axis == 1 else (-1, 1)
        q = np.clip(np.round(weight / scale.reshape(shape)), -127, 127).astype(np.int8)
        graph.initializer.remove(initializers[name])
        graph.initializer.extend(
            [
                numpy_helper.from_array(q, f"{name}_q"),
                numpy_helper.from_array(scale, f"{name}_scale"),
                numpy_helper.from_array(np.zeros(scale.shape, np.int8), f"{name}_zero"),
            ]
        )
        dequant_nodes.append(
            helper.make_node(
                "DequantizeLinear", [f"{name}_q", f"{name}_scale", f"{name}_zero"], [name], axis=axis, name=f"{name}_dq"
            )
        )
    for index, node in enumerate(dequant_nodes):
        graph.node.insert(index, node)
    onnx.save(model, str(dst))


#: Cau mau de tu kiem tra ban ONNX ngay khi xuat (ca an toan lan nguy hiem, ca dai lan ngan).
_VERIFY_TEXTS = (
    "cô my đây con làm bài tập nhé",
    "Thầy Nam thể dục đây, nạp hộ thầy 2 thẻ Viettel 100k vào số này gấp",
    "Mai nhớ mang vở bài tập Toán nhé, cô kiểm tra 15 phút đấy!",
    "Nhập mã OTP vừa gửi về điện thoại để nhận 1000 Robux miễn phí tại robux-thcs.vip",
    "Quy khach da su dung 90% dung luong goi cuoc. Soan MI10 gui 9123 de mua them.",
    "x",
)


def _verify_onnx(onnx_path: Path, model, tokenizer, tolerance: float = 0.02) -> None:
    """So ban ONNX voi PyTorch; lech qua nguong thi dung lai (khong phat hanh mo hinh hong)."""
    try:
        import numpy as np
        import onnxruntime as ort
    except ImportError:
        logger.warning("Không có onnxruntime - bỏ qua bước tự kiểm tra bản ONNX.")
        return
    import torch

    session = ort.InferenceSession(str(onnx_path))
    worst = 0.0
    for text in _VERIFY_TEXTS:
        enc = tokenizer(text, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            expected = torch.softmax(model(**enc).logits[0], -1).numpy()
        logits = session.run(
            None, {"input_ids": enc["input_ids"].numpy(), "attention_mask": enc["attention_mask"].numpy()}
        )[0][0]
        got = np.exp(logits - logits.max())
        got /= got.sum()
        worst = max(worst, float(np.abs(got - expected).max()))
        if got.argmax() != expected.argmax():
            raise RuntimeError(f"Bản ONNX đổi nhãn so với PyTorch ở câu: {text!r}")
    if worst > tolerance:
        raise RuntimeError(f"Bản ONNX lệch PyTorch {worst:.4f} (> {tolerance}).")
    logger.info("Bản ONNX khớp PyTorch (lệch xác suất lớn nhất %.5f).", worst)


def export_phobert(out_dir: Path, model_dir: Optional[Path] = None, quantize: bool = True) -> Optional[Dict]:
    """Xuat PhoBERT da tinh chinh sang ONNX (trong so int8) chia manh + tokenizer.json.

    Tra ve ``manifest`` (danh sach manh tep) hoac ``None`` neu chua co mo hinh.
    """
    from app.transformer_model import MAX_LENGTH, TRANSFORMER_DIR

    model_dir = Path(model_dir or TRANSFORMER_DIR)
    if not (model_dir / "config.json").exists():
        return None
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.eval()
    meta_path = model_dir / "label_map.json"
    labels = json.loads(meta_path.read_text())["labels"] if meta_path.exists() else [0, 1, 2]

    out_dir.mkdir(parents=True, exist_ok=True)
    fp32_path = out_dir / "model.fp32.onnx"
    sample = tokenizer("cô my đây con làm bài tập nhé", return_tensors="pt")

    class _Logits(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, input_ids, attention_mask):
            return self.inner(input_ids=input_ids, attention_mask=attention_mask).logits

    # .eval() cho ca lop boc: torch.onnx.export tra lai che do cu cua module sau khi xuat,
    # neu de mac dinh (train) thi dropout bat lai va lam sai buoc tu kiem tra phia duoi.
    wrapper = _Logits(model).eval()
    with torch.no_grad():
        torch.onnx.export(
            wrapper,
            (sample["input_ids"], sample["attention_mask"]),
            str(fp32_path),
            input_names=["input_ids", "attention_mask"],
            output_names=["logits"],
            dynamic_axes={
                "input_ids": {0: "batch", 1: "sequence"},
                "attention_mask": {0: "batch", 1: "sequence"},
                "logits": {0: "batch"},
            },
            opset_version=17,
            dynamo=False,
        )
    model.eval()

    final_path = out_dir / "model.onnx"
    if quantize:
        quantize_weights_int8(fp32_path, final_path)
        fp32_path.unlink()
    else:
        fp32_path.replace(final_path)

    _verify_onnx(final_path, model, tokenizer)

    data = final_path.read_bytes()
    final_path.unlink()
    parts = []
    for i in range(0, len(data), CHUNK_BYTES):
        name = f"model.onnx.part{len(parts):02d}"
        (out_dir / name).write_bytes(data[i : i + CHUNK_BYTES])
        parts.append({"file": name, "size": len(data[i : i + CHUNK_BYTES])})

    (out_dir / "tokenizer.json").write_text(
        json.dumps(export_phobert_tokenizer(tokenizer, labels, MAX_LENGTH), ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    import hashlib

    manifest = {
        "version": hashlib.sha256(data).hexdigest()[:12],
        "parts": parts,
        "totalBytes": len(data),
        "quantization": "int8-weights" if quantize else "none",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
