# DANH MỤC BỘ DỮ LIỆU LIÊN QUAN

Tài liệu này liệt kê các nguồn dữ liệu **có thật, kiểm chứng được** dùng để huấn luyện
và kiểm định hệ thống, kèm giấy phép và cách tích hợp. Bộ dữ liệu do nhóm tự sinh
(`data/dataset_thcs_scam.jsonl`) chỉ mô phỏng ngữ cảnh học đường, nên mọi con số đo
trên đó đều lạc quan — phần này giải quyết đúng điểm yếu ấy.

---

## 1. Đã tích hợp sẵn (chạy một lệnh là có)

```bash
python scripts/fetch_external_datasets.py --list   # xem danh mục
python scripts/fetch_external_datasets.py          # tải bộ mặc định
python scripts/update_blocklist.py                 # tải danh sách đen tên miền
```

### 1.1. Quality-Assured Vietnamese SMS Phishing Dataset ⭐ quan trọng nhất

| Thuộc tính | Thông tin |
| :--- | :--- |
| Nguồn | https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_dataset |
| Quy mô | 2.991 tin nhắn SMS **thật** (2.193 hợp lệ / 798 lừa đảo) |
| Nhãn | Nhị phân: `0` = hợp lệ, `1` = rác/lừa đảo |
| Giấy phép | CC BY 4.0 (ghi nguồn khi sử dụng) |
| Đặc điểm | Đã ẩn danh PII (`[PHONE]`, `[MONEY]`…); ~53% viết không dấu; có sẵn train/test chống rò rỉ |
| Đạo đức | Thu thập tự nguyện, có đồng thuận, miễn thẩm định IRB (mã `IRB-2026-NLP-0428`) |

**Lưu ý khác miền dữ liệu:** bộ này thiên về SMS ngân hàng/viễn thông của người lớn,
không phải tin nhắn học đường. Vì vậy nó dùng để **kiểm tra độ bền** và huấn luyện lớp
mô hình tổng quát, chứ không thay thế được dữ liệu của học sinh THCS.

Trích dẫn:
> Tran, N. T. T.; Le, H. K.; Nguyen, M. T.; Nguyen, V. T.; Mai, H. D.
> *Vietnamese SMS Dataset with Quality Assurance*. IEEE Access, 2026.

### 1.2. URLhaus (abuse.ch) — danh sách đen tên miền

| Thuộc tính | Thông tin |
| :--- | :--- |
| Nguồn | https://urlhaus.abuse.ch/downloads/text_online/ |
| Nội dung | URL độc hại **đang hoạt động**, cập nhật liên tục |
| Giấy phép | CC0 |
| Cách dùng | `scripts/update_blocklist.py` → `data/blocklist_domains.txt` → `app/link_analyzer.py` |

Tên miền nằm trong danh sách đen được coi là bằng chứng chắc chắn (`LINK_BLOCKLISTED`),
không cần suy đoán thêm. Danh sách đen được gửi kèm cả bản demo tĩnh nên bản web cũng biết.

---

## 2. Nguồn có thể bổ sung (chưa tích hợp)

| Bộ dữ liệu | Quy mô / nội dung | Giấy phép | Vì sao hữu ích |
| :--- | :--- | :--- | :--- |
| [trannguyenthaituan/vietnamese_sms_phishing_sample](https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_phishing_sample) | 300 tin (bản rút gọn của 1.1) | CC BY 4.0 | Chạy thử nhanh, tiện cho máy yếu |
| [ViSpamReviews (UIT-NLP)](https://github.com/sonlam1102/vispamdetection) | Bình luận rác trên sàn thương mại điện tử tiếng Việt | Liên hệ tác giả (sonlt@uit.edu.vn) | Văn phong spam tiếng Việt; PhoBERT đạt ~86,9% macro-F1 trên bộ này |
| [ucirvine/sms_spam](https://huggingface.co/datasets/ucirvine/sms_spam) | 5.574 SMS tiếng Anh (ham/spam) | Công cộng (UCI) | Kiểm tra sức mạnh của đặc trưng char n-gram ngoài tiếng Việt |
| [ealvaradob/phishing-dataset](https://huggingface.co/datasets/ealvaradob/phishing-dataset) | Email + URL + SMS phishing (tiếng Anh) | Xem thẻ dữ liệu | Mẫu câu lừa đảo kinh điển, có thể dịch để làm giàu dữ liệu |
| [pirocheto/phishing-url](https://huggingface.co/datasets/pirocheto/phishing-url) · [Mitake/PhishingURLsANDBenignURLs](https://huggingface.co/datasets/Mitake/PhishingURLsANDBenignURLs) | URL lừa đảo và URL lành tính | Xem thẻ dữ liệu | Huấn luyện riêng một bộ phân loại URL thay cho luật thủ công |
| [Content-based Approach for Vietnamese Spam SMS Filtering](https://arxiv.org/pdf/1705.04003) | Bài báo mô tả bộ 6.599 SMS tiếng Việt (Viettel, Vinaphone) | Xin phép tác giả | Bộ dữ liệu tiếng Việt lớn, có thể liên hệ xin |
| [vn-badsite-filter](https://github.com/curbengh/vn-badsite-filter) | Danh sách trang độc hại nhắm vào người Việt (nguồn chongluadao.vn) | CC0 / MIT | ⚠️ Nguồn đã **ngừng cập nhật từ 05/2025** — chỉ còn giá trị tham khảo |

---

## 3. Tự thu thập dữ liệu học đường (việc quan trọng nhất còn lại)

Đây là phần **không bộ dữ liệu công khai nào thay thế được**, vì tin nhắn lừa đảo nhắm
vào học sinh THCS (nạp thẻ game, mạo danh thầy cô) hầu như không xuất hiện trong các bộ
SMS ngân hàng. Gợi ý quy trình, học theo cách nhóm tác giả bộ 1.1 đã làm:

1. **Xin phép trước.** Có sự đồng ý của nhà trường, phụ huynh và chính học sinh.
   Nói rõ: thu gì, dùng làm gì, ai được xem, khi nào xóa.
2. **Ẩn danh ngay khi thu.** Thay số điện thoại, tên người, số tài khoản bằng token
   (`[PHONE]`, `[NAME]`, `[BANK_ACC]`) — làm trước khi lưu, không làm sau.
3. **Gán nhãn hai vòng.** Hai bạn gán độc lập theo bộ quy tắc viết sẵn, lệch nhau thì
   người thứ ba quyết định. Ghi lại tỉ lệ đồng thuận (Cohen's kappa) để đưa vào báo cáo.
4. **Chia tập kiểm thử trước khi nhìn dữ liệu**, tránh vô tình chỉnh luật theo tập kiểm thử.
5. **Mục tiêu tối thiểu:** 300–500 tin nhắn thật là đủ để đánh giá đáng tin cậy;
   1.000+ tin thì có thể huấn luyện lại mô hình.

Dữ liệu tự thu xong có thể chuyển về đúng định dạng của dự án (xem `app/datasets.py`),
rồi huấn luyện chung với các nguồn trên:

```bash
python scripts/train_model.py \
    --dataset data/dataset_thcs_scam.jsonl \
    --dataset data/external/vi_sms_phishing.jsonl \
    --dataset data/truong_minh_thu_thap.jsonl \
    --split-mode split
```

---

## 4. Nguyên tắc khi dùng dữ liệu của người khác

* **Giữ đúng giấy phép.** CC BY 4.0 bắt buộc ghi nguồn — đã ghi sẵn trong
  `data/external/*_meta.json` và trong mục trích dẫn ở trên.
* **Không commit dữ liệu ngoài vào kho mã nguồn.** `data/external/` đã nằm trong
  `.gitignore`; ai cần thì chạy lệnh tải về.
* **Không công bố lại dữ liệu thô của người khác** trong poster hay báo cáo; chỉ trích
  vài ví dụ minh họa kèm nguồn.
* **Cẩn thận với dữ liệu cá nhân.** Tin nhắn thật có thể chứa thông tin riêng tư;
  luôn ẩn danh trước khi lưu hoặc mang đi đâu khác.
