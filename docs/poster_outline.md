# DÀN Ý POSTER & BÀI THUYẾT MINH KHKT
## "Lá Chắn Số — Hệ thống AI cảnh báo tin nhắn lừa đảo cho học sinh THCS"

> Khổ poster gợi ý: A0 dọc (841 × 1189 mm). Chữ tiêu đề ≥ 90 pt, chữ nội dung ≥ 28 pt,
> đọc được từ khoảng cách 1,5 m. Mỗi khối dưới đây tương ứng một ô trên poster.

---

## Ô 1 — Tiêu đề (đỉnh poster)

* **Tên đề tài:** Lá Chắn Số — Nghiên cứu và xây dựng hệ thống AI nhận diện, cảnh báo tin nhắn
  lừa đảo và nâng cao kỹ năng an toàn số cho học sinh THCS.
* Tên nhóm tác giả · Lớp · Trường · Giáo viên hướng dẫn.
* Lĩnh vực: Hệ thống phần mềm / Trí tuệ nhân tạo (Xử lý ngôn ngữ tự nhiên).
* Dải 3 màu 🟢🟡🔴 chạy ngang làm nhận diện thị giác của cả poster.

## Ô 2 — Lý do chọn đề tài (góc trên trái)

* Học sinh THCS dùng điện thoại sớm nhưng kinh nghiệm phòng vệ còn ít.
* 4 kịch bản lừa đảo nhắm thẳng vào lứa tuổi này:
  nạp thẻ game · mạo danh thầy cô · trúng thưởng ảo · đe dọa chiếm tài khoản.
* Các công cụ chống lừa đảo hiện có chủ yếu dành cho người lớn, dùng tiếng Anh,
  chỉ trả lời "an toàn / không an toàn" mà **không giải thích** và **không dạy** kỹ năng.
* 👉 *Khoảng trống:* cần một công cụ **nói được vì sao** bằng ngôn ngữ học sinh hiểu.

## Ô 3 — Mục tiêu & Tính mới

| Mục tiêu | Tính mới |
|---|---|
| Phân loại 3 mức rủi ro 🟢🟡🔴 | Giao diện 3 màu, một ô nhập, một nút bấm |
| Giải thích được lý do (XAI) | Chỉ thẳng cụm từ nguy hiểm **trong chính tin nhắn của em** |
| Dạy kỹ năng ngay lúc cảnh báo | Flashcard + mini-quiz 30 giây gắn đúng kịch bản vừa gặp |
| Hiểu cách gõ của học sinh | Nhận cả tin **không dấu** và **teen-code** (`0tp` → `otp`) |

## Ô 4 — Sơ đồ hệ thống (ô lớn, trung tâm poster)

```
Tin nhắn / Ảnh chụp màn hình
   → Module 1: Làm sạch, OCR, trích URL–SĐT–tiền–OTP
   → Module 2: 35 luật + 9 luật kết hợp + mô hình TF-IDF  →  🟢 / 🟡 / 🔴 + BẰNG CHỨNG
   → Module 3: Việc cần làm ngay + Flashcard + Mini-quiz
   → Module 4: Một API duy nhất cho giao diện web
```

* In kèm **ảnh chụp màn hình kết quả thật** của tin nhắn mạo danh thầy cô (phần bôi vàng rất dễ hiểu).

## Ô 5 — Điểm kỹ thuật cốt lõi (nếu ban giám khảo hỏi sâu)

1. **Ba lớp nhận diện bổ sung nhau:** bộ luật (giải thích được) · phân tích tên miền
   (danh sách trắng + danh sách đen cộng đồng) · mô hình học máy TF-IDF và PhoBERT
   (bắt cách diễn đạt mới). Lớp nào thiếu thì hệ thống vẫn chạy.
2. **Cộng điểm kiểu noisy-OR** `1 − ∏(1 − wᵢ)`: nhiều dấu hiệu yếu cộng lại thành một
   cảnh báo mạnh, điểm luôn nằm trong khoảng [0, 1].
3. **Luật kết hợp:** "mạo danh + đòi tiền", "quà miễn phí + link lạ" → kết luận nguy hiểm ngay,
   mô phỏng cách suy luận của con người.
4. **Phủ quyết hai chiều:** mô hình có thể *kéo lên* (khi rất chắc là lừa đảo) và
   *kéo xuống* (khi rất chắc là an toàn). Cơ chế thứ hai ra đời sau khi đo trên dữ liệu
   thật — xem Ô 6.
5. **Ánh xạ vị trí ký tự:** mọi bằng chứng được trích **nguyên văn** từ tin nhắn gốc,
   kể cả khi hệ thống xử lý trên bản đã khử dấu.
6. **Một bộ luật, hai nơi chạy:** bản web tĩnh dùng `engine.js` sinh từ chính mã nguồn Python;
   có bài kiểm thử đối chiếu từng tin nhắn để hai bản không bao giờ lệch nhau.

## Ô 6 — Kết quả: đo trên HAI miền dữ liệu

**Miền học đường (dữ liệu nhóm tự sinh, 1.800 mẫu)**

| Chỉ tiêu | Yêu cầu | Đạt được |
| :--- | :--- | :--- |
| Accuracy | ≥ 90% | 98,2% (bộ luật) → 100% (có lớp học máy) |
| Recall nhãn 🔴 | ≥ 95% | 100% |
| Độ trễ | < 1000 ms | ~2 ms |

**Miền tin nhắn THẬT (2.991 SMS do người dùng đóng góp, CC BY 4.0)** — đây mới là phép thử thật:

| Cấu hình | Accuracy | Recall | Báo động nhầm |
| :--- | ---: | ---: | ---: |
| Bộ luật — phiên bản đầu | 45,4% | 40,4% | 52,7% |
| Bộ luật — sau khi phân tích lỗi và sửa | 65,8% | 65,3% | 34,0% |
| **Cả ba lớp** (tập test 597 tin chưa từng thấy) | **85,9%** | **94,9%** | 17,3% |

* Cấu hình "bộ luật + PhoBERT" đạt accuracy cao nhất **87,8%** (bỏ sót nhiều hơn một chút).
  Nhóm chọn cấu hình bỏ sót ít nhất làm mặc định, đúng tinh thần "thà báo động nhầm còn hơn bỏ sót".
* Kiểm thử tự động: **100/100 bài đạt**, gồm cả bài đối chiếu Python ↔ JavaScript.
* 12 tin nhắn hoàn toàn mới: đúng 11/12 (lỗi duy nhất là **báo dư**, không bỏ sót).

👉 **Điểm nhấn khi thuyết trình:** nhóm không giấu con số 45,4% ban đầu. Chính nó chỉ ra
những lỗi thật (bộ luật cũ coi `viettel.vn` là trang giả mạo; báo đỏ mọi tin ngân hàng
*thông báo* mã OTP) và dẫn tới các cải tiến ở Ô 5.

## Ô 7 — Khảo sát thực nghiệm (Mục 6.2 của đặc tả)

* Mẫu: 30–50 học sinh THCS · thiết kế **trước – sau**.
* Quy trình: kiểm tra nhận diện lừa đảo (10 câu) → dùng ứng dụng 1 tuần → kiểm tra lại (10 câu tương đương).
* Chỉ số theo dõi: điểm trung bình, tỉ lệ nhận đúng tin 🔴, số học sinh biết "3 bước vàng".
* Mục tiêu: điểm sau tăng **> 35%** so với trước.
* Trình bày bằng biểu đồ cột ghép **Trước / Sau**, kèm ảnh buổi thử nghiệm tại lớp.

## Ô 8 — Hạn chế & Hướng phát triển

**Hạn chế (nêu thẳng, đây là điểm cộng khi phản biện):**
dữ liệu còn là mô phỏng · mới xử lý tiếng Việt dạng chữ · kẻ lừa đảo luôn đổi cách viết.

**Hướng phát triển:**
tiện ích Chrome & ứng dụng Android cảnh báo ngay trong Zalo/Messenger ·
thu thập tin nhắn thật (ẩn danh, có sự đồng ý) để huấn luyện lại ·
bảng theo dõi cho giáo viên chủ nhiệm · nâng cấp mô hình lên PhoBERT.

## Ô 9 — Chân poster

* Mã QR trỏ tới **bản demo trực tuyến trên GitHub Pages** (chạy ngay trong trình duyệt,
  không cần cài gì) và kho mã nguồn.
* Danh mục tài liệu tham khảo.
* Câu chốt in đậm: **"Dừng lại — Kiểm chứng — Báo người lớn."**
