# KỊCH BẢN DEMO 3 PHÚT TRƯỚC BAN GIÁM KHẢO

**Chuẩn bị trước khi vào phòng thi**

* Chạy sẵn `uvicorn app.main:app` và **mở sẵn trang** `http://127.0.0.1:8000` (đã bấm thử 1 lần
  để trình duyệt tải xong giao diện).
* Trang demo vẫn hiển thị tốt **khi không có Internet** (đã có sẵn CSS dự phòng) — cứ yên tâm.
* Mở thêm một tab `http://127.0.0.1:8000/docs` phòng khi giám khảo muốn xem API.
* Phân vai: **HS1** nói, **HS2** thao tác máy.

---

## 0:00 – 0:25 · Mở đầu bằng một câu chuyện có thật

> **HS1:** "Kính chào ban giám khảo. Tuần trước, một bạn trong lớp em nhận được tin nhắn:
> *'Thầy Nam thể dục đây, nạp hộ thầy 2 thẻ Viettel 100k, mai thầy gửi lại'*. Bạn ấy đã nạp thật.
> Đó không phải thầy Nam — đó là kẻ lừa đảo dùng tài khoản bị hack.
> Nhóm em xây dựng **Lá Chắn Số** để không còn bạn nào mất tiền như vậy nữa."

## 0:25 – 0:45 · Vấn đề & khoảng trống

> **HS1:** "Học sinh THCS là mục tiêu của 4 chiêu lừa quen thuộc: nạp thẻ game, mạo danh thầy cô,
> trúng thưởng ảo, và đe dọa chiếm tài khoản. Các công cụ hiện có chỉ nói 'an toàn' hay 'nguy hiểm',
> mà **không giải thích vì sao** và **không dạy** cho tụi em cách tự nhận ra lần sau."

## 0:45 – 1:35 · Demo chính (HS2 thao tác)

**Bước 1 — Dán tin nhắn mạo danh thầy cô** (bấm nút ví dụ *"Mạo danh thầy cô"*).

> **HS1:** "Chưa tới **một phần trăm giây**, hệ thống trả về đèn đỏ: *Cảnh báo lừa đảo, hãy dừng lại ngay*."

**Bước 2 — Chỉ vào phần bôi vàng trong tin nhắn.**

> "Đây là điểm khác biệt của đề tài: AI **chỉ thẳng ba cụm từ** đã tố cáo kẻ lừa đảo —
> *'Thầy Nam thể dục đây'* là mạo danh, *'nạp hộ thầy'* là đòi tiền, *'gấp'* là tạo áp lực thời gian.
> Học sinh không chỉ được cảnh báo, mà **hiểu được vì sao**."

**Bước 3 — Kéo xuống phần *Em nên làm gì* và mini-quiz.**

> "Kèm theo là các bước xử lý ngay, một thẻ ghi nhớ, và một câu hỏi 30 giây để biến kiến thức
> thành phản xạ." *(HS2 bấm một đáp án để giám khảo thấy phần chấm điểm và giải thích.)*

**Bước 4 — Dán tin nhắn bình thường** (bấm ví dụ *"Tin nhắn an toàn"*).

> "Với tin nhắn học tập bình thường, hệ thống trả về đèn xanh — công cụ **không gây hoang mang**."

## 1:35 – 2:15 · Cách hệ thống hoạt động

*(HS2 mở tab `/docs` hoặc chỉ vào sơ đồ trên poster.)*

> **HS1:** "Hệ thống có 4 module. Module 1 làm sạch tin nhắn — kể cả khi bạn em gõ **không dấu**
> hay viết *'0tp'* thay cho *'OTP'*. Module 2 là bộ não: **35 luật nhận diện** cùng **9 luật kết hợp**,
> ví dụ 'mạo danh' cộng 'đòi tiền' là kết luận nguy hiểm ngay; song song đó là một **mô hình học máy
> TF-IDF** để bắt những cách nói mới. Module 3 sinh lời khuyên và mini-quiz. Module 4 gộp tất cả
> vào một API duy nhất cho giao diện."

> "Chúng em cố ý để bộ luật quyết định phần giải thích, vì **học máy không nói được lý do**,
> mà với học sinh thì lý do mới là thứ dạy được kỹ năng."

## 2:15 – 2:40 · Kết quả & sự trung thực về số liệu

> **HS1:** "Trên bộ dữ liệu nhóm em tự sinh, hệ thống đạt **100%**. Nhưng tụi em không dừng
> ở đó. Nhóm em tải về **2.991 tin nhắn lừa đảo thật** do người dùng đóng góp, và chạy lại —
> kết quả chỉ còn **45%**."

> "Con số đó chỉ cho tụi em thấy những lỗi thật: bộ luật cũ coi cả `viettel.vn` là trang giả
> mạo, và báo động đỏ với mọi tin ngân hàng *thông báo* mã OTP. Sau khi sửa, và sau khi cho
> mô hình học từ dữ liệu thật, độ chính xác trên **tập kiểm thử chưa từng thấy** đạt
> **85,9%**, bắt được **94,9%** tin lừa đảo — chỉ còn bỏ sót 8 trên 158 tin."

> "Điều tụi em tự hào không phải là con số 100%, mà là việc tụi em đã tự tìm ra được mình
> sai ở đâu và sửa được."

## 2:40 – 3:00 · Hướng phát triển & chốt

> **HS1:** "Sắp tới nhóm em sẽ làm tiện ích Chrome và ứng dụng Android để cảnh báo ngay trong
> Zalo, Messenger; đồng thời khảo sát 30–50 bạn trước và sau một tuần sử dụng để đo mức tiến bộ."

> "Điều tụi em mong nhất là mỗi bạn học sinh đều nhớ ba bước: **Dừng lại — Kiểm chứng — Báo người lớn.**
> Em xin hết. Nhóm em sẵn sàng trả lời câu hỏi ạ."

---

## Phụ lục — Câu hỏi phản biện thường gặp

| Câu hỏi | Gợi ý trả lời |
|---|---|
| "Khác gì bộ lọc từ khóa thông thường?" | Từ khóa đơn lẻ không kết luận. Hệ thống chấm điểm theo trọng số, có **luật kết hợp** (mạo danh + đòi tiền), có tín hiệu **an toàn kéo điểm xuống**, và luôn kèm bằng chứng. "Nạp thẻ" trong câu bình thường không đủ để báo đỏ. |
| "Sao không dùng ChatGPT/mô hình lớn?" | Cần chạy được **ngoại tuyến, miễn phí, dưới 1 giây** trên máy trường học, và cần **giải thích được** cùng một cách mọi lúc. Mô hình lớn tốn phí, cần mạng và có thể trả lời khác nhau cho cùng một tin nhắn. |
| "Nếu kẻ lừa đảo đổi cách viết thì sao?" | Đã xử lý hai lớp: khử teen-code (`0tp`→`otp`, `m4t kh4u`→`mật khẩu`) và mô hình học máy bắt cách diễn đạt mới. Bộ luật thiết kế dạng bảng dữ liệu nên thêm chiêu mới chỉ mất vài dòng. |
| "Dữ liệu tự sinh thì kết quả có đáng tin không?" | Đúng, nên nhóm đã kiểm định trên **2.991 tin nhắn thật** (bộ dữ liệu CC BY 4.0 của nhóm tác giả Việt Nam, xem `docs/datasets.md`). Điểm tụt từ 100% xuống 45%, nhóm phân tích lỗi, sửa, rồi đạt 85,9% accuracy và 94,9% recall trên tập test chưa từng thấy. Bước tiếp theo là thu thập 300–500 tin nhắn thật của học sinh, ẩn danh và có sự đồng ý. |
| "Sao không dùng luôn mô hình lớn như PhoBERT ngay từ đầu?" | Hệ thống **có** lớp PhoBERT (mã nguồn mở, VinAI). Nhưng học máy không giải thích được "vì sao", mà với học sinh thì lý do mới dạy được kỹ năng. Vì vậy bộ luật giữ phần giải thích, mô hình giữ phần bao phủ. |
| "Bản demo trên web có gửi tin nhắn của em đi đâu không?" | Không. Bản trên GitHub Pages chạy **hoàn toàn trong trình duyệt** — tin nhắn không rời khỏi máy. Bản có máy chủ cũng không lưu nội dung tin nhắn vào cơ sở dữ liệu nào. |
| "Tin nhắn của học sinh có bị lưu lại không?" | Không. Hệ thống xử lý và trả kết quả ngay trong bộ nhớ, không có cơ sở dữ liệu lưu nội dung tin nhắn. |
| "AI báo sai thì sao?" | Giao diện luôn hiển thị dòng nhắc: kết quả chỉ mang tính cảnh báo, khi nghi ngờ hãy hỏi bố mẹ hoặc thầy cô. Hệ thống hỗ trợ chứ không thay thế người lớn. |
