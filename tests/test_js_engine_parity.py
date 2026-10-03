"""Kiem tra ban JavaScript (chay tren GitHub Pages) cho ket qua GIONG ban Python.

Bo demo tinh khong co may chu, no chay bang `frontend/engine.js`. Neu hai ban
lech nhau thi hoc sinh xem tren web se nhan canh bao khac voi he thong that,
nen phep so sanh nay duoc dua vao kiem thu tu dong (va vao workflow Pages).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from app.classifier import analyze
from app.config import BASE_DIR, DATASET_DEMO
from app.engine_export import build_engine_data

NODE = shutil.which("node")
ENGINE_JS = BASE_DIR / "frontend" / "engine.js"

RUNNER = """
const fs = require('fs');
const Engine = require(process.argv[2]);
const data = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const texts = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const extra = process.argv[5] ? JSON.parse(fs.readFileSync(process.argv[5], 'utf8')) : {};
const Models = require(process.argv[2].replace(/engine[.]js$/, 'models.js'));
const engine = Engine.create(data, extra.tfidf ? { tfidf: Models.createTfidf(extra.tfidf) } : {});
console.log(JSON.stringify(texts.map((t, i) => {
  const tr = extra.transformerScores ? extra.transformerScores[i] : null;
  const r = engine.analyze(t, tr ? { transformerScores: tr } : {});
  return { level: r.verdict.level, score: r.meta.risk_score, category: r.meta.scam_category };
})));
"""


def _run_js(texts, extra=None):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "extra.json").write_text(json.dumps(extra or {}, ensure_ascii=False), encoding="utf-8")
        (tmp / "runner.js").write_text(RUNNER, encoding="utf-8")
        (tmp / "data.json").write_text(json.dumps(build_engine_data(), ensure_ascii=False), encoding="utf-8")
        (tmp / "texts.json").write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [NODE, str(tmp / "runner.js"), str(ENGINE_JS), str(tmp / "data.json"), str(tmp / "texts.json"), str(tmp / "extra.json")],
            capture_output=True, text=True, timeout=180,
        )
    if result.returncode != 0:
        raise AssertionError(f"Chạy engine.js thất bại:\n{result.stderr}")
    return json.loads(result.stdout)


pytestmark = pytest.mark.skipif(NODE is None, reason="Không có Node.js để chạy engine.js")


def _load_demo_texts():
    if not DATASET_DEMO.exists():
        pytest.skip("Chưa sinh dữ liệu demo. Chạy: python data/generate_sample_dataset.py")
    with DATASET_DEMO.open(encoding="utf-8") as fh:
        return [json.loads(line)["text"] for line in fh if line.strip()]


def test_js_engine_matches_python_on_demo_dataset():
    texts = _load_demo_texts()
    js_results = _run_js(texts)
    assert len(js_results) == len(texts)
    for text, js in zip(texts, js_results):
        py = analyze(text, use_ml=False)
        assert py.risk_level == js["level"], f"Lệch mức cảnh báo ở: {text[:70]}"
        assert abs(py.risk_score - js["score"]) < 0.005, f"Lệch điểm rủi ro ở: {text[:70]}"
        assert py.scam_category == js["category"], f"Lệch kịch bản ở: {text[:70]}"


def test_js_engine_handles_tricky_inputs():
    texts = [
        "cho anh xin m4 0tp ngay",                       # teen-code
        "thay Nam day, nap ho thay 100k gap",            # không dấu
        "Truy cập https://viettel.vn/xacthucTB ngay",    # tên miền chính thống
        "vao https://vietcombank.vn-gll.top de xac minh",  # tên miền giả mạo
        "Mai nhớ mang vở bài tập Toán nhé!",             # an toàn
        "cô my đây con làm bài tập nhé",                 # thầy cô tự xưng + bài tập
    ]
    for text, js in zip(texts, _run_js(texts)):
        py = analyze(text, use_ml=False)
        assert py.risk_level == js["level"], f"Lệch ở: {text}"


def _fake_transformer_scores(text):
    """Diem PhoBERT gia lap (on dinh theo noi dung) de kiem tra cong thuc tron diem."""
    h = sum(ord(c) * (i + 1) for i, c in enumerate(text)) % 1000 / 1000
    safe, susp = 0.85 * h, 0.15 * (1 - h)
    return {"SAFE": safe, "SUSPICIOUS": susp, "DANGEROUS": 1 - safe - susp}


def test_js_engine_matches_python_with_model_layers(monkeypatch):
    """Ban web co TF-IDF + PhoBERT phai tron diem giong het app/classifier.py."""
    pytest.importorskip("sklearn")
    from app import ml_model, transformer_model
    from app.model_export import export_tfidf

    texts = _load_demo_texts()
    labels = [json.loads(line)["label"] for line in DATASET_DEMO.open(encoding="utf-8") if line.strip()]
    pipeline = ml_model.train(texts, labels)
    monkeypatch.setattr(ml_model, "_model", pipeline)
    monkeypatch.setattr(ml_model, "_model_loaded", True)
    monkeypatch.setattr(transformer_model, "predict_proba", _fake_transformer_scores)

    texts = texts + ["cô my đây con làm bài tập nhé", "cho anh xin m4 0tp ngay", "Mai nhớ mang vở bài tập Toán nhé!"]
    extra = {
        "tfidf": export_tfidf(pipeline),
        "transformerScores": [_fake_transformer_scores(t.strip()) for t in texts],
    }
    for text, js in zip(texts, _run_js(texts, extra)):
        py = analyze(text, use_ml=True)
        assert py.ml_scores and py.transformer_scores
        assert py.risk_level == js["level"], f"Lệch mức cảnh báo ở: {text[:70]}"
        assert abs(py.risk_score - js["score"]) < 0.005, f"Lệch điểm rủi ro ở: {text[:70]}"
        assert py.scam_category == js["category"], f"Lệch kịch bản ở: {text[:70]}"


def test_js_tfidf_matches_sklearn_probabilities():
    pytest.importorskip("sklearn")
    from app import ml_model
    from app.model_export import export_tfidf

    texts = _load_demo_texts()
    labels = [json.loads(line)["label"] for line in DATASET_DEMO.open(encoding="utf-8") if line.strip()]
    pipeline = ml_model.train(texts, labels)
    probes = [ml_model.normalize_for_model(t) for t in texts] + ["a b  c", "x", "nap the 100k https://bit.ly/abc"]
    expected = pipeline.predict_proba(probes)
    script = """
const M = require(process.argv[2]);
const fs = require('fs');
const tf = M.createTfidf(JSON.parse(fs.readFileSync(process.argv[3], 'utf8')));
const texts = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
console.log(JSON.stringify(texts.map((t) => { const p = tf.predict(t); return [p.SAFE, p.SUSPICIOUS, p.DANGEROUS]; })));
"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "run.js").write_text(script, encoding="utf-8")
        (tmp / "model.json").write_text(json.dumps(export_tfidf(pipeline)), encoding="utf-8")
        (tmp / "texts.json").write_text(json.dumps(probes, ensure_ascii=False), encoding="utf-8")
        out = subprocess.run(
            [NODE, str(tmp / "run.js"), str(BASE_DIR / "frontend" / "models.js"), str(tmp / "model.json"), str(tmp / "texts.json")],
            capture_output=True, text=True, timeout=120, check=True,
        )
    for row_py, row_js in zip(expected, json.loads(out.stdout)):
        assert max(abs(a - b) for a, b in zip(row_py, row_js)) < 1e-4


def test_js_phobert_tokenizer_matches_python():
    """Bo tach tu BPE viet lai bang JS phai cho dung day ma token nhu PhobertTokenizer."""
    pytest.importorskip("transformers")
    from transformers import AutoTokenizer

    from app.model_export import export_phobert_tokenizer
    from app.transformer_model import DEFAULT_BASE_MODEL, MAX_LENGTH, TRANSFORMER_DIR

    source = TRANSFORMER_DIR if (TRANSFORMER_DIR / "config.json").exists() else DEFAULT_BASE_MODEL
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(source))
    except Exception:  # pragma: no cover - khong co mang / chua tai mo hinh
        pytest.skip("Không nạp được tokenizer PhoBERT.")
    if not hasattr(tokenizer, "bpe_ranks"):
        pytest.skip("Tokenizer không phải PhobertTokenizer (BPE).")

    texts = _load_demo_texts() + ["cô my đây con làm bài tập nhé", "😀😀 a\nb\n\n c", "x" * 400]
    expected = [tokenizer(t, truncation=True, max_length=MAX_LENGTH)["input_ids"] for t in texts]
    script = """
const M = require(process.argv[2]);
const fs = require('fs');
const tk = M.createPhobertTokenizer(JSON.parse(fs.readFileSync(process.argv[3], 'utf8')));
const texts = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
console.log(JSON.stringify(texts.map((t) => tk.encode(t))));
"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "run.js").write_text(script, encoding="utf-8")
        spec = export_phobert_tokenizer(tokenizer, [0, 1, 2], MAX_LENGTH)
        (tmp / "tok.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        (tmp / "texts.json").write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
        out = subprocess.run(
            [NODE, str(tmp / "run.js"), str(BASE_DIR / "frontend" / "models.js"), str(tmp / "tok.json"), str(tmp / "texts.json")],
            capture_output=True, text=True, timeout=120, check=True,
        )
    for text, py_ids, js_ids in zip(texts, expected, json.loads(out.stdout)):
        assert py_ids == js_ids, f"Lệch token ở: {text[:60]}"