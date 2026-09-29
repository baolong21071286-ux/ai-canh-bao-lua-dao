# NHẬT KÝ CẢI THIỆN MÔ HÌNH

Tài liệu ghi lại quá trình **đo — tìm lỗi — sửa — đo lại**. Đây cũng là phần trả lời
cho câu hỏi hay gặp nhất của ban giám khảo: *"Làm sao biết hệ thống chạy tốt thật?"*

---

## Giai đoạn 0 — Điểm số ban đầu và vì sao không tin được

Phiên bản đầu đạt **99,2% accuracy** trên bộ dữ liệu 1.800 mẫu. Nhưng bộ dữ liệu đó do
chính nhóm sinh ra từ 68 mẫu câu, và bộ luật cũng được tinh chỉnh trên nó — nói cách khác
hệ thống đang *tự chấm bài của mình*.

## Giai đoạn 1 — Đối mặt với dữ liệu thật

Nhóm tải bộ **Quality-Assured Vietnamese SMS Phishing Dataset** (2.991 tin nhắn SMS thật,
CC BY 4.0, xem `docs/datasets.md`) và chạy lại đúng hệ thống đó.

| Chỉ số (🟡+🔴 tính là "có cảnh báo") | Kết quả |
| :--- | :--- |
| Accuracy | **0,4544** |
| Recall (bắt được lừa đảo) | 0,4035 |
| Tỉ lệ báo động nhầm | **52,7%** |

Điểm rơi từ 99% xuống 45%. Đây mới là con số thật, và nó cho thấy khoảng cách giữa
"dữ liệu mình tự nghĩ ra" và "tin nhắn ngoài đời".

## Giai đoạn 2 — Phân tích lỗi

Thống kê luật nào gây báo động nhầm nhiều nhất và đọc các tin bị bỏ sót:

| Nguyên nhân | Ví dụ thật | Cách sửa |
| :--- | :--- | :--- |
| Luật link coi **mọi** tên miền chứa tên thương hiệu là giả mạo | `viettel.vn`, `momo.vn` bị báo đỏ | Xây `app/domains.py` + `app/link_analyzer.py` với **danh sách trang chính thống**; chỉ cảnh báo khi tên thương hiệu nằm trên tên miền lạ |
| Không phân biệt *thông báo* OTP với *đòi* OTP | "Mã OTP xác thực GD là 066595" bị báo đỏ | Thêm luật an toàn `SAFE_OTP_NOTIFICATION` + cơ chế **khử nhiễu** (`RULE_SUPPRESSIONS`) |
| "nạp thẻ", "ví điện tử", "ưu đãi" bị tính là bằng chứng | Tin khuyến mãi hợp lệ của nhà mạng | Chuyển thành **luật khuếch đại** (chỉ tính khi đã có tín hiệu rủi ro khác) |
| Khớp nhầm vào giữa chuỗi số | `500.000d` khớp luật "nạp 000d" | Thêm ranh giới `(?<![\d.,])` |
| Thiếu kịch bản lừa đảo ngân hàng | "tài khoản bị đăng nhập ở thiết bị khác, vào link…" | Thêm luật `PHISH_LOGIN_ALERT`, mở rộng `THREAT_ACCOUNT_LOCK` (tạm ngưng/hạn chế/phong tỏa) |
| Thiếu kịch bản cờ bạc trá hình | "tân thủ nhận lộc, nạp đầu nhân đôi" | Thêm danh mục `GAMBLING_SCAM` + luật + flashcard + quiz |
| Tên miền viết sai một chữ | `vietinbamk.com`, `i-sacombank.com` | Phát hiện bằng khoảng cách Levenshtein tới tên thương hiệu thật |

## Giai đoạn 3 — Kết quả sau khi sửa bộ luật

| Chỉ số (🟡+🔴) | Trước | Sau |
| :--- | ---: | ---: |
| Accuracy | 0,4544 | **0,6580** |
| Recall | 0,4035 | **0,6529** |
| F1 | 0,2830 | **0,5046** |
| Báo động nhầm | 52,7% | 34,0% |

Đồng thời **không làm hỏng miền học đường**: bộ demo 60 tin vẫn đạt 100%, bộ 1.800 mẫu
vẫn đạt 99,2%.

> Bài học: luật viết tay rất tốt để *giải thích*, nhưng không thể phủ hết một miền dữ liệu
> mà mình không lường trước. Muốn tiến xa hơn phải học từ dữ liệu thật.

## Giai đoạn 4 — Để mô hình học từ dữ liệu thật

Huấn luyện lại lớp TF-IDF trên **dữ liệu kết hợp** (1.800 mẫu học đường + 2.394 SMS thật),
đánh giá trên tập test thật đã tách sẵn (597 tin, chống rò rỉ dữ liệu):

| Nhãn | Precision | Recall | F1 | Số mẫu |
| :--- | ---: | ---: | ---: | ---: |
| 🟢 An toàn | 0,9785 | 0,9339 | 0,9557 | 439 |
| 🔴 Lừa đảo | 0,8371 | **0,9430** | 0,8869 | 158 |
| **Accuracy** | | | **0,9363** | 597 |

Chỉ bỏ sót 9/158 tin lừa đảo — so với 507 tin bỏ sót của bộ luật thuần.

## Giai đoạn 4b — Một phát hiện bất ngờ: thêm bộ luật vào lại làm *giảm* chất lượng

Khi ghép bộ luật với TF-IDF và đo trên tập test thật, kết quả **thấp hơn** so với dùng
riêng TF-IDF (0,79 so với 0,94). Lý do: bộ luật được viết cho ngữ cảnh học đường, mang
sang miền SMS ngân hàng/khuyến mãi thì nó liên tục đẩy điểm rủi ro lên, kéo cả những tin
mà mô hình đã khẳng định là an toàn lên mức 🟡.

Cách xử lý — cho mô hình **quyền phủ quyết theo chiều an toàn**: nếu mô hình rất chắc chắn
tin nhắn an toàn (P(🟢) ≥ 0,80) *và* bộ luật không nắm bằng chứng chắc chắn nào
(`hard_danger`), điểm rủi ro bị nhân với 0,40 (`MODEL_SAFE_VETO` trong `app/config.py`).

Hai tham số này được chọn **trên tập train**, rồi mới đo một lần trên tập test — để con số
báo cáo không bị "tinh chỉnh theo đáp án".

| Cấu hình (tập test thật, 597 tin chưa từng thấy) | Accuracy | Recall | F1 | Báo nhầm | Bỏ sót |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Chỉ bộ luật | 0,6097 | 0,4494 | 0,3787 | 146 | 87 |
| Bộ luật + TF-IDF (chưa có phủ quyết) | 0,7940 | 0,9873 | 0,7172 | 121 | 2 |
| **Bộ luật + TF-IDF (có phủ quyết)** | **0,8593** | 0,9367 | **0,7789** | **74** | 10 |

Miền học đường không hề bị ảnh hưởng: vẫn 100% trên bộ 1.800 mẫu.

> Bài học: một lớp mạnh ở miền này có thể là gánh nặng ở miền khác. Hệ thống lai cần cơ chế
> để các lớp *sửa lưng nhau theo cả hai chiều*, chứ không chỉ cộng điểm.

Công cụ đo: `python scripts/compare_layers.py --dataset <tệp> --binary`.

## Giai đoạn 5 — Thêm mô hình ngôn ngữ mã nguồn mở (PhoBERT)

`scripts/train_transformer.py` tinh chỉnh **PhoBERT-base-v2** (VinAI Research, giấy phép MIT)
trên cùng bộ dữ liệu kết hợp. PhoBERT hiểu ngữ cảnh tiếng Việt nên bắt được những cách
diễn đạt mà TF-IDF (chỉ đếm từ) bỏ lỡ.

_(Kết quả đo xem bảng "Kết quả đánh giá" trong README.)_

---

## Kiến trúc hợp nhất cuối cùng

```
              ┌── Bộ luật (35+ luật, giải thích được)       trọng số 0,65
Tin nhắn ─────┼── TF-IDF + Logistic Regression              trọng số 0,35
              └── PhoBERT (tuỳ chọn)                        trọng số 0,50
                        ↓
        điểm rủi ro = trung bình có trọng số (lớp nào thiếu thì chia lại trọng số)
                        ↓
        🟢 < 0,26 ≤ 🟡 < 0,58 ≤ 🔴      + bằng chứng LUÔN lấy từ bộ luật
```

Ba nguyên tắc giữ nguyên xuyên suốt:

1. **Phần giải thích cho học sinh luôn đến từ bộ luật** — mô hình học máy không nói được
   "vì sao", mà với học sinh thì lý do mới là thứ dạy được kỹ năng.
2. **Thiếu lớp nào vẫn chạy** — tải kho mã nguồn về là dùng được ngay với bộ luật.
3. **Thà báo động nhầm còn hơn bỏ sót** — mọi ngưỡng đều ưu tiên Recall ở nhãn 🔴.

## Việc nên làm tiếp

1. **Thu thập 300–500 tin nhắn thật của học sinh** (xem quy trình trong `docs/datasets.md`).
   Đây là việc có ích nhất còn lại — không nguồn công khai nào thay được.
2. **Hiệu chỉnh xác suất** (Platt scaling / isotonic) để `confidence_score` phản ánh đúng
   xác suất thật, thay vì chỉ là điểm số quy đổi.
3. **Học chủ động (active learning):** ghi lại các tin mà hệ thống phân vân (điểm quanh
   ngưỡng 0,26 và 0,58), ưu tiên gán nhãn chính những tin đó.
4. **Cập nhật danh sách đen định kỳ** bằng `scripts/update_blocklist.py`.
5. **Rút gọn mô hình** (distillation / ONNX) nếu muốn chạy PhoBERT ngay trong tiện ích trình duyệt.
