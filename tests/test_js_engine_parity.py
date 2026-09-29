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
const engine = Engine.create(data);
console.log(JSON.stringify(texts.map((t) => {
  const r = engine.analyze(t);
  return { level: r.verdict.level, score: r.meta.risk_score, category: r.meta.scam_category };
})));
"""


def _run_js(texts):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "runner.js").write_text(RUNNER, encoding="utf-8")
        (tmp / "data.json").write_text(json.dumps(build_engine_data(), ensure_ascii=False), encoding="utf-8")
        (tmp / "texts.json").write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [NODE, str(tmp / "runner.js"), str(ENGINE_JS), str(tmp / "data.json"), str(tmp / "texts.json")],
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
    ]
    for text, js in zip(texts, _run_js(texts)):
        py = analyze(text, use_ml=False)
        assert py.risk_level == js["level"], f"Lệch ở: {text}"
