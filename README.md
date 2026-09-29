# 🛡️ Lá Chắn Số — Hệ thống AI cảnh báo tin nhắn lừa đảo cho học sinh THCS

Hệ thống AI nhận diện và cảnh báo tin nhắn có dấu hiệu lừa đảo, **giải thích được lý do cảnh báo**
và kèm theo flashcard + mini-quiz giúp học sinh THCS (11–15 tuổi) rèn phản xạ an toàn số.

Toàn bộ mã nguồn được xây dựng theo *Đặc tả kỹ thuật hệ thống* (4 module, 3 mức rủi ro 🟢🟡🔴).

---

## 1. Kiến trúc

```
Tin nhắn (text) / Ảnh chụp màn hình
      │
      ▼
┌──────────────────────────────────────────────────┐
│ Module 1 · app/preprocessor.py                   │  OCR (tùy chọn), chuẩn hóa tiếng Việt,
│   làm sạch + trích xuất URL, SĐT, tiền, OTP      │  khử "teen-code" (0tp → otp)
└─────────────────────┬────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────┐
│ Module 2 · Ba lớp nhận diện chạy song song        │
│   ① app/rules.py       35+ luật regex có trọng số │ → bằng chứng giải thích được
│   ② app/link_analyzer.py  phân tích tên miền      │ → danh sách trắng + danh sách đen
│   ③ app/ml_model.py TF-IDF · app/transformer_model.py PhoBERT │ → bắt cách nói mới
│   app/classifier.py hợp nhất + 9 luật kết hợp     │
└─────────────────────┬────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────┐
│ Module 3 · app/education.py                      │  hành động khẩn cấp + flashcard
│   + app/education_content.py                     │  + mini-quiz 30 giây
└─────────────────────┬────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────┐
│ Module 4 · app/pipeline.py + app/main.py         │  1 request → đủ dữ liệu hiển thị
└─────────────────────┬────────────────────────────┘
                      ▼
      frontend/index.html — chạy được ở 2 chế độ:
        • có máy chủ  → dùng đầy đủ cả 3 lớp
        • không máy chủ (GitHub Pages / mất mạng) → frontend/engine.js
```

### Vì sao dùng mô hình lai (hybrid)?

| Lớp | Điểm mạnh | Điểm yếu |
| :--- | :--- | :--- |
| Bộ luật regex có trọng số | Giải thích được từng cụm từ, chạy < 1 ms, sửa nhanh khi có chiêu lừa mới | Không phủ hết cách diễn đạt |
| Phân tích tên miền | Biết `viettel.vn` là thật còn `vietcombank.vn-gll.top` là giả; dùng được danh sách đen cộng đồng | Chỉ áp dụng cho tin có link |
| TF-IDF + Logistic Regression | Học từ dữ liệu, nhẹ, nhanh | Chỉ đếm từ, không hiểu ngữ cảnh |
| PhoBERT (tùy chọn) | Hiểu ngữ cảnh tiếng Việt, mạnh nhất | Nặng hơn, cần cài `torch` |

Điểm rủi ro cuối cùng là **trung bình có trọng số** của các lớp đang có; lớp nào thiếu thì
trọng số được chia lại, nên hệ thống chạy được ngay cả khi chỉ có bộ luật.
**Bằng chứng hiển thị cho học sinh luôn đến từ bộ luật**, vì mô hình học máy không nói được "vì sao".

## 2. Cài đặt & chạy thử

```bash
pip install -r requirements.txt

# 1) Sinh bộ dữ liệu mô phỏng (60 mẫu demo + 1800 mẫu huấn luyện)
python data/generate_sample_dataset.py

# 2) (Nên làm) Tải dữ liệu tin nhắn lừa đảo THẬT + danh sách đen tên miền
python scripts/fetch_external_datasets.py
python scripts/update_blocklist.py

# 3) Huấn luyện mô hình trên dữ liệu kết hợp
python scripts/train_model.py \
    --dataset data/dataset_thcs_scam.jsonl \
    --dataset data/external/vi_sms_phishing.jsonl --split-mode split

# 4) (Tùy chọn) Thêm lớp PhoBERT — mạnh nhất nhưng cần torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers
python scripts/train_transformer.py \
    --dataset data/dataset_thcs_scam.jsonl \
    --dataset data/external/vi_sms_phishing.jsonl --split-mode split

# 5) Chạy máy chủ API + giao diện web
uvicorn app.main:app --reload
#   Giao diện demo : http://127.0.0.1:8000
#   Tài liệu API   : http://127.0.0.1:8000/docs

# 6) Kiểm thử và đánh giá
pytest -q
python scripts/evaluate.py                                           # dữ liệu học đường (3 mức)
python scripts/evaluate.py --dataset data/external/vi_sms_phishing.jsonl --binary   # dữ liệu thật
```

Bước 1 là đủ để hệ thống chạy — các bước sau chỉ làm nó mạnh hơn.

OCR ảnh chụp màn hình là **tùy chọn**, cần cài thêm ở mức hệ điều hành:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-vie
```

Khi chưa cài, API trả lỗi `503` kèm hướng dẫn, các chức năng còn lại không bị ảnh hưởng.

---

## 2b. Bản demo trực tuyến (GitHub Pages)

Bản demo **tĩnh** chạy hoàn toàn trong trình duyệt — không cần máy chủ Python, không gửi
tin nhắn của học sinh đi đâu cả:

```bash
python scripts/build_static_site.py   # xuất ra thư mục site/
python -m http.server -d site 8080    # xem thử tại http://127.0.0.1:8080
```

Toàn bộ luật, ngưỡng và nội dung giáo dục được xuất từ chính mã nguồn Python ra
`engine-data.json` (xem `app/engine_export.py`), rồi chạy bằng `frontend/engine.js`.
Bài kiểm thử `tests/test_js_engine_parity.py` đối chiếu hai bản trên từng tin nhắn để
bảo đảm chúng **không bao giờ lệch nhau**.

Phát hành tự động bằng GitHub Actions (`.github/workflows/pages.yml`):

1. Vào **Settings → Pages → Build and deployment → Source: “GitHub Actions”** (chỉ làm một lần).
2. Đẩy mã nguồn lên nhánh chính → workflow tự dựng và xuất bản.
3. Trang demo xuất hiện tại `https://<tên-tài-khoản>.github.io/Fraud-message-detection/`.

Muốn tạo bản phát hành kèm tệp tải về: `git tag v1.0.0 && git push origin v1.0.0`
(workflow `.github/workflows/release.yml` sẽ đóng gói bản demo tĩnh và bộ dữ liệu).

## 3. Danh sách API

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/scan/preprocess` | Module 1 — làm sạch + trích xuất thực thể (JSON hoặc multipart ảnh) |
| POST | `/api/v1/scan/analyze` | Module 2 — phân loại 3 mức + bằng chứng giải thích |
| POST | `/api/v1/scan/educate` | Module 3 — hành động khuyến nghị + flashcard + quiz |
| POST | `/api/v1/scan/quick-check` | **Module 4 — endpoint chính cho giao diện** |
| GET | `/api/v1/learn/flashcards` | Danh sách flashcard |
| GET | `/api/v1/learn/quizzes` | Danh sách mini-quiz |
| POST | `/api/v1/learn/quiz/check` | Chấm điểm câu trả lời của học sinh |
| GET | `/api/v1/health` | Trạng thái hệ thống (số luật, mô hình ML, OCR) |
| GET | `/api/v1/meta/categories` | Danh mục kịch bản lừa đảo & mã màu |

### Ví dụ

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scan/quick-check \
  -H "Content-Type: application/json" \
  -d '{"content":"Nhập mã OTP vừa gửi về điện thoại để nhận 1000 Robux miễn phí tại web robux-thcs.vip","channel":"Discord"}'
```

```json
{
  "code": 200,
  "result": {
    "verdict": {
      "level": "DANGEROUS",
      "badge_title": "Cực kỳ nguy hiểm - Đánh cắp mã OTP / mật khẩu",
      "theme_color": "#E53E3E",
      "confidence_score": 0.99
    },
    "summary": "Tin nhắn lừa đảo chiếm đoạt mã OTP/mật khẩu tài khoản của em.",
    "highlight_words": ["Nhập mã OTP", "nhận 1000 Robux", "robux-thcs.vip"],
    "immediate_actions": ["1. Không gửi mã OTP, mật khẩu cho bất kỳ ai, ..."],
    "interactive_quiz": { "question": "Mã OTP dùng để làm gì...", "correct": "B" }
  }
}
```

Thêm `"include_details": true` để nhận kèm dữ liệu thô của cả 3 module (rất hữu ích khi thuyết minh).

---

## 4. Bộ dữ liệu

### 4.1. Dữ liệu mô phỏng (có sẵn trong kho mã nguồn)

| Tệp | Số mẫu | Mục đích |
| :--- | :--- | :--- |
| `data/dataset_demo_60.jsonl` | 60 | Bộ viết tay, dùng để demo và kiểm thử |
| `data/dataset_thcs_scam.jsonl` | 1.800 | Bộ huấn luyện, sinh từ 60 mẫu gốc + 68 mẫu câu có khe điền |

Cơ cấu đúng theo đặc tả: **40% an toàn · 20% nghi vấn · 40% nguy hiểm**.
Khoảng 25% số mẫu được viết **không dấu** để mô hình quen với cách gõ của học sinh.

```json
{"id": "MSG_0012", "text": "Ban la nguoi may man trung 1 xe dap dien VinFast...",
 "label": 2, "label_name": "DANGEROUS", "category": "FAKE_PRIZE",
 "template_id": "SEED_D15", "risk_entities": ["trung 1", "xe dap dien VinFast"]}
```

Sinh lại với quy mô khác: `python data/generate_sample_dataset.py --size 3000`.

### 4.2. Dữ liệu THẬT tải từ bên ngoài

```bash
python scripts/fetch_external_datasets.py --list    # xem danh mục
python scripts/fetch_external_datasets.py           # tải bộ mặc định
```

| Nguồn | Quy mô | Giấy phép |
| :--- | :--- | :--- |
| [Quality-Assured Vietnamese SMS Phishing Dataset](https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_dataset) | 2.991 SMS thật (798 lừa đảo) | CC BY 4.0 |
| [URLhaus (abuse.ch)](https://urlhaus.abuse.ch) — danh sách đen tên miền | cập nhật hằng ngày | CC0 |

Dữ liệu ngoài **không được commit** (tôn trọng giấy phép gốc), nằm trong `data/external/`
cùng tệp `*_meta.json` ghi rõ nguồn và cách trích dẫn.
Danh mục đầy đủ các bộ dữ liệu liên quan, kèm hướng dẫn tự thu thập dữ liệu học đường
đúng chuẩn đạo đức: **[`docs/datasets.md`](docs/datasets.md)**.

---

## 5. Kết quả đánh giá

Hệ thống được đo trên **hai miền dữ liệu khác nhau** — đây là điểm quan trọng nhất khi
đọc các con số dưới đây.

### 5.1. Miền học đường — dữ liệu mô phỏng do nhóm sinh (1.800 mẫu)

| Cấu hình | Accuracy | Recall 🔴 | Bỏ sót 🔴→🟢 | Độ trễ TB |
| :--- | ---: | ---: | ---: | ---: |
| Chỉ bộ luật | 0,9817 | **1,0000** | 0 | 0,4 ms |
| Bộ luật + TF-IDF | **1,0000** | **1,0000** | 0 | 2,1 ms |
| Bộ luật + PhoBERT | **1,0000** | **1,0000** | 0 | 55,9 ms |
| Cả ba lớp *(mặc định)* | **1,0000** | **1,0000** | 0 | 59,3 ms |

Trên bộ demo 60 tin viết tay: **60/60 đúng** ở mọi cấu hình.

> ⚠️ Bộ dữ liệu này do nhóm tự sinh và bộ luật cũng được tinh chỉnh trên nó, nên điểm số
> ở đây là **điểm trong mẫu** — không phải năng lực thật ngoài đời. Mục 5.2 mới là phép thử thật.

### 5.2. Miền tin nhắn THẬT — 2.991 SMS do người dùng đóng góp (CC BY 4.0)

Đây mới là con số trung thực. Nhãn của bộ này là nhị phân nên đánh giá ở chế độ
"có cảnh báo (🟡 hoặc 🔴)" so với "an toàn".

**(a) Bộ luật trước và sau khi phân tích lỗi** — đo trên toàn bộ 2.991 tin:

| Bộ luật | Accuracy | Recall | F1 | Báo động nhầm |
| :--- | ---: | ---: | ---: | ---: |
| Phiên bản đầu | 0,4544 | 0,4035 | 0,2830 | 52,7% |
| Sau khi sửa theo phân tích lỗi | **0,6580** | **0,6529** | **0,5046** | 34,0% |

**(b) Khi có thêm lớp học máy** — đo trên tập test 597 tin **đã tách sẵn, chống rò rỉ dữ
liệu, mô hình chưa từng thấy** (`python scripts/compare_layers.py --binary`):

| Cấu hình | Accuracy | Recall | F1 | Tin hợp lệ bị báo nhầm | Bỏ sót | Độ trễ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Chỉ bộ luật | 0,6097 | 0,4494 | 0,3787 | 146/439 | 87/158 | 0,8 ms |
| Bộ luật + TF-IDF | 0,8593 | 0,9367 | 0,7789 | 74/439 | 10/158 | 2,9 ms |
| Bộ luật + PhoBERT | **0,8777** | 0,9367 | **0,8022** | **63/439** | 10/158 | 81,6 ms |
| Cả ba lớp *(mặc định)* | 0,8593 | **0,9494** | 0,7812 | 76/439 | **8/158** | 85,7 ms |

Hai cấu hình cuối là hai lựa chọn có chủ đích: **cả ba lớp** bỏ sót ít nhất (8/158 tin lừa đảo)
nên được đặt làm mặc định theo đúng tinh thần "thà báo động nhầm còn hơn bỏ sót";
**bộ luật + PhoBERT** cho độ chính xác cao nhất nếu muốn ít phiền hà hơn.

Riêng mô hình PhoBERT chạy độc lập trên cùng tập test: accuracy **0,9363**,
recall nhãn lừa đảo **0,9241** (`python scripts/train_transformer.py`).

Quá trình "đo → tìm lỗi → sửa → đo lại" được ghi đầy đủ trong
**[`docs/model_improvements.md`](docs/model_improvements.md)** — trong đó có những lỗi
thật đã phát hiện nhờ dữ liệu thật, ví dụ bộ luật cũ coi `viettel.vn` là trang giả mạo,
hay báo đỏ mọi tin ngân hàng *thông báo* mã OTP.

### 5.3. Kiểm tra bằng tin nhắn hoàn toàn mới

12 tin nhắn do nhóm tự viết, **không nằm trong bất kỳ bộ dữ liệu nào và không dùng để
chỉnh luật**: đúng **11/12**. Lỗi duy nhất là một tin thu quỹ lớp thật bị cảnh báo mức 🟡 —
tức là **báo dư chứ không bỏ sót**, đúng hướng thiết kế.

### 5.4. Đối chiếu với chỉ tiêu của đặc tả (Mục 6.1)

| Chỉ tiêu | Yêu cầu | Miền học đường | Miền SMS thật (tập test) |
| :--- | :--- | :--- | :--- |
| Accuracy | ≥ 90% | ✅ 98,2% (bộ luật) · 100% (có học máy) | ⚠️ 87,8% (tốt nhất) · 61,0% (chỉ bộ luật) |
| Recall nhãn 🔴 | ≥ 95% | ✅ 100% | ⚠️ 94,9% (cả ba lớp) · 44,9% (chỉ bộ luật) |
| Độ trễ suy luận | < 1000 ms | ✅ 2 ms (không PhoBERT) · 58 ms (có PhoBERT) | ✅ 86 ms |

Kết luận trung thực: **hệ thống vượt chỉ tiêu trong miền học đường; trên miền SMS thật thì
gần đạt khi có lớp học máy (94,9% so với yêu cầu 95%), còn bộ luật thủ công thì chưa đủ.**
Đó chính là lý do kiến trúc giữ cả ba lớp — và cũng là lý do việc cần làm tiếp theo là thu
thập tin nhắn thật của học sinh THCS.

---

## 6. Cấu trúc dự án

```
app/
  config.py             Ngưỡng rủi ro, mã màu, danh mục kịch bản, trọng số các lớp
  text_utils.py         Chuẩn hóa tiếng Việt, khử teen-code, ánh xạ vị trí để trích bằng chứng
  rules.py              35+ luật nhận diện (regex + trọng số + lý do giải thích)
  domains.py            Danh sách trang chính thống, thương hiệu, danh sách đen
  link_analyzer.py      Chấm điểm tên miền (giả mạo / gõ nhái / ngẫu nhiên / bị tố cáo)
  preprocessor.py       Module 1 — làm sạch & trích xuất thực thể
  classifier.py         Module 2 — hợp nhất các lớp, luật kết hợp, sinh bằng chứng
  ml_model.py           Lớp TF-IDF + Logistic Regression (tùy chọn)
  transformer_model.py  Lớp PhoBERT (tùy chọn)
  education_content.py  Kho flashcard / mini-quiz / hành động theo 13 kịch bản
  education.py          Module 3 — sinh lời khuyên & chấm điểm quiz
  pipeline.py           Module 4 — gộp toàn trình
  engine_export.py      Xuất toàn bộ luật ra JSON cho bản chạy trong trình duyệt
  datasets.py           Nạp/chia dữ liệu dùng chung cho các script
  ocr.py                Đọc chữ từ ảnh chụp màn hình (tùy chọn)
  main.py               REST API (FastAPI)
data/generate_sample_dataset.py    Sinh bộ dữ liệu mô phỏng
scripts/fetch_external_datasets.py Tải bộ dữ liệu thật từ bên ngoài
scripts/update_blocklist.py        Cập nhật danh sách đen tên miền (URLhaus)
scripts/train_model.py             Huấn luyện TF-IDF (hỗ trợ nhiều nguồn dữ liệu)
scripts/train_transformer.py       Tinh chỉnh PhoBERT
scripts/evaluate.py                Đánh giá theo chỉ tiêu Mục 6.1 (có chế độ nhị phân)
scripts/build_static_site.py       Dựng bản demo tĩnh cho GitHub Pages
frontend/index.html                Giao diện web (tự chuyển sang chạy offline khi không có máy chủ)
frontend/engine.js                 Bản JavaScript của Module 1–3
.github/workflows/pages.yml        Tự động phát hành demo lên GitHub Pages
.github/workflows/release.yml      Đóng gói bản phát hành khi gắn thẻ phiên bản
tests/                             91 bài kiểm thử tự động (gồm đối chiếu Python ↔ JavaScript)
docs/datasets.md                   Danh mục bộ dữ liệu + hướng dẫn tự thu thập
docs/model_improvements.md         Nhật ký đo — tìm lỗi — sửa — đo lại
docs/poster_outline.md             Dàn ý poster KHKT
docs/demo_script_3min.md           Kịch bản demo 3 phút
```

---

## 7. Giới hạn đã biết

1. **Chưa có dữ liệu tin nhắn thật của học sinh THCS.** Bộ dữ liệu thật đang dùng là SMS
   ngân hàng/viễn thông của người lớn — khác miền. Việc cần làm nhất là thu thập 300–500
   tin nhắn thật từ học sinh (quy trình và nguyên tắc đạo đức ở `docs/datasets.md`).
2. **Khôi phục dấu tiếng Việt theo từ điển** — chỉ phủ khoảng 150 từ thuộc ngữ cảnh lừa đảo
   học đường. Việc *nhận diện* không phụ thuộc bước này (luật đối chiếu bản không dấu).
3. **Danh sách trang chính thống là thủ công** — một trang con hợp lệ chưa có trong danh sách
   vẫn bị cảnh báo mức vàng. Đây là đánh đổi có chủ đích theo hướng an toàn.
4. **Chỉ xử lý tiếng Việt dạng chữ** — chưa xử lý giọng nói, video, sticker.
5. **OCR phụ thuộc Tesseract** — chất lượng giảm rõ với ảnh chụp mờ hoặc nền tối.
6. **Kẻ lừa đảo luôn đổi cách viết** — cần cập nhật luật và huấn luyện lại định kỳ; đó là lý do
   hệ thống giữ song song lớp học máy và danh sách đen cộng đồng.
7. Hệ thống là **công cụ hỗ trợ cảnh báo**, không thay thế việc hỏi ý kiến bố mẹ và thầy cô.
