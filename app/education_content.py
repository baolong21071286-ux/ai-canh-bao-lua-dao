"""Kho noi dung giao duc: hanh dong khuyen nghi, flashcard va mini-quiz.

Toan bo noi dung duoc viet cho lua tuoi 11-15: cau ngan, khong hu doa, co huong
dan hanh dong cu the. Moi kich ban co 1 flashcard va >= 2 cau quiz de hoc sinh
khong bi lap lai cau hoi khi dung nhieu lan.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.config import (
    CATEGORY_ACCOUNT_THREAT,
    CATEGORY_GAMBLING,
    CATEGORY_ADS_SPAM,
    CATEGORY_FAKE_PRIZE,
    CATEGORY_GAME_TOPUP,
    CATEGORY_IMPERSONATION_RELATIVE,
    CATEGORY_IMPERSONATION_TEACHER,
    CATEGORY_JOB_SCAM,
    CATEGORY_OTP_PHISHING,
    CATEGORY_PHISHING_LINK,
    CATEGORY_SAFE,
    CATEGORY_SUSPICIOUS_INVITE,
)

# Ba buoc "xuong song" ap dung cho moi tinh huong nguy hiem: DUNG LAI - KIEM CHUNG - BAO NGUOI LON.
GOLDEN_RULES = [
    "DỪNG LẠI: không trả lời, không bấm, không chuyển gì cả.",
    "KIỂM CHỨNG: gọi điện trực tiếp cho người thật qua số đã lưu.",
    "BÁO NGƯỜI LỚN: kể ngay với bố mẹ hoặc thầy cô chủ nhiệm.",
]

CONTENT: Dict[str, Dict[str, Any]] = {
    CATEGORY_IMPERSONATION_TEACHER: {
        "primary_warning": "TUYỆT ĐỐI KHÔNG làm theo và KHÔNG nạp thẻ.",
        "steps": [
            "1. Không gửi mã thẻ cào hoặc tiền cho người gửi.",
            "2. Chụp ảnh màn hình lưu lại bằng chứng.",
            "3. Báo ngay với thầy cô chủ nhiệm hoặc bố mẹ để kiểm chứng.",
            "4. Gọi vào số điện thoại chính thức của thầy cô (số bố mẹ đã lưu) để xác minh.",
        ],
        "flashcard": {
            "card_id": "FC_IMP_01",
            "title": "Cảnh giác khi 'Thầy cô' nhờ nạp tiền",
            "tip": "Khi nhận tin nhắn nhờ nạp tiền từ người tự xưng là thầy cô, hãy gọi điện thoại trực tiếp cho số điện thoại chính thức của thầy cô để xác minh.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_IMP_01",
                "question": "Nếu tài khoản mạng xã hội của giáo viên nhắn tin nhờ em nạp giúp 100k thẻ điện thoại, em sẽ làm gì?",
                "options": [
                    {"id": "A", "text": "Nạp ngay để lấy điểm cao môn đó"},
                    {"id": "B", "text": "Hỏi mượn tiền bạn bè nạp giúp vì thầy bảo đang gấp"},
                    {"id": "C", "text": "Không nạp tiền, báo ngay với bố mẹ hoặc liên hệ thầy cô trực tiếp"},
                ],
                "correct_option": "C",
                "explanation": "Tài khoản của thầy cô có thể đã bị kẻ xấu hack để đi lừa đảo. Thầy cô không bao giờ nhờ học sinh nạp tiền theo cách này.",
            },
            {
                "quiz_id": "QZ_IMP_02",
                "question": "Cách kiểm chứng nhanh nhất khi 'thầy cô' nhắn tin nhờ chuyển khoản gấp là gì?",
                "options": [
                    {"id": "A", "text": "Nhắn lại hỏi thầy có đúng là thầy không"},
                    {"id": "B", "text": "Gọi điện vào số điện thoại chính thức của thầy cô mà bố mẹ đã lưu"},
                    {"id": "C", "text": "Hỏi trong nhóm chat lớp xem bạn nào chuyển trước"},
                ],
                "correct_option": "B",
                "explanation": "Kẻ xấu đang cầm tài khoản đó nên nhắn lại vẫn là nói chuyện với kẻ xấu. Chỉ cuộc gọi tới số đã biết mới xác minh được người thật.",
            },
        ],
    },
    CATEGORY_IMPERSONATION_RELATIVE: {
        "primary_warning": "KHÔNG chuyển tiền khi chưa gọi điện xác minh người thật.",
        "steps": [
            "1. Không chuyển khoản, không gửi mã thẻ cào.",
            "2. Gọi điện thoại (gọi thường, không gọi qua mạng xã hội) cho người đó để kiểm chứng.",
            "3. Kể lại với bố mẹ dù em chưa gửi gì cả.",
            "4. Nếu tài khoản bạn bị hack, nhắc bạn đổi mật khẩu và báo cho cả lớp cùng biết.",
        ],
        "flashcard": {
            "card_id": "FC_REL_01",
            "title": "'Bạn thân' hỏi vay tiền gấp?",
            "tip": "Tài khoản bạn bè rất dễ bị chiếm. Hãy gọi điện trực tiếp cho bạn trước khi làm bất cứ điều gì liên quan tới tiền.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_REL_01",
                "question": "Nick Facebook của bạn thân nhắn: 'Cho tao mượn 200k, gấp lắm, mai trả'. Em nên làm gì?",
                "options": [
                    {"id": "A", "text": "Chuyển ngay vì là bạn thân"},
                    {"id": "B", "text": "Gọi điện thoại trực tiếp cho bạn để hỏi lại"},
                    {"id": "C", "text": "Nhắn lại hỏi mật khẩu để kiểm tra có đúng bạn không"},
                ],
                "correct_option": "B",
                "explanation": "Đây là chiêu chiếm tài khoản rất phổ biến. Một cuộc gọi 10 giây giúp em không mất tiền.",
            },
            {
                "quiz_id": "QZ_REL_02",
                "question": "Dấu hiệu nào cho thấy 'người thân' nhắn tin có thể là giả mạo?",
                "options": [
                    {"id": "A", "text": "Dùng số lạ, hối thúc gấp và yêu cầu chuyển tiền"},
                    {"id": "B", "text": "Hỏi thăm chuyện học hành ở lớp"},
                    {"id": "C", "text": "Nhắc em nhớ ăn cơm đúng giờ"},
                ],
                "correct_option": "A",
                "explanation": "Số lạ + hối thúc + tiền là bộ ba dấu hiệu lừa đảo quen thuộc nhất.",
            },
        ],
    },
    CATEGORY_GAME_TOPUP: {
        "primary_warning": "KHÔNG nạp thẻ, KHÔNG đưa tài khoản game cho người lạ.",
        "steps": [
            "1. Không nạp tiền, không gửi mã thẻ, không cho mượn tài khoản game.",
            "2. Thoát khỏi trang web/nhóm chat đó ngay.",
            "3. Kiểm tra sự kiện trên trang chính thức của nhà phát hành game.",
            "4. Kể với bố mẹ nếu em đã lỡ nhập thông tin.",
        ],
        "flashcard": {
            "card_id": "FC_GAME_01",
            "title": "Không có Robux/Kim cương miễn phí",
            "tip": "Mọi lời hứa tặng vật phẩm game miễn phí kèm điều kiện 'nạp trước' hoặc 'đăng nhập tại đây' đều là lừa đảo.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_GAME_01",
                "question": "Một trang web hứa tặng 10.000 Robux miễn phí nếu em đăng nhập tài khoản Roblox. Em nên?",
                "options": [
                    {"id": "A", "text": "Đăng nhập thử, nếu không được thì thôi"},
                    {"id": "B", "text": "Không đăng nhập, vì đó là bẫy đánh cắp tài khoản"},
                    {"id": "C", "text": "Rủ bạn cùng đăng nhập cho chắc"},
                ],
                "correct_option": "B",
                "explanation": "Trang web giả sẽ lấy mật khẩu của em ngay khi em bấm 'đăng nhập'. Nhà phát hành không bao giờ tặng quà theo cách này.",
            },
            {
                "quiz_id": "QZ_GAME_02",
                "question": "'Nạp 100k tặng 1000 kim cương, chỉ hôm nay' — điều gì đáng ngờ nhất ở đây?",
                "options": [
                    {"id": "A", "text": "Số kim cương quá nhiều"},
                    {"id": "B", "text": "Yêu cầu nạp tiền trước cho người lạ và hối thúc thời gian"},
                    {"id": "C", "text": "Tên game không quen thuộc"},
                ],
                "correct_option": "B",
                "explanation": "Nạp tiền cho người lạ + hối thúc 'chỉ hôm nay' là công thức chung của lừa đảo.",
            },
        ],
    },
    CATEGORY_FAKE_PRIZE: {
        "primary_warning": "KHÔNG nộp bất kỳ khoản phí nào để 'nhận thưởng'.",
        "steps": [
            "1. Không chuyển phí vận chuyển, phí hồ sơ hay bất cứ khoản nào.",
            "2. Không bấm vào link trong tin nhắn trúng thưởng.",
            "3. Tự hỏi: mình có tham gia chương trình này bao giờ chưa?",
            "4. Cho bố mẹ xem tin nhắn trước khi làm bất cứ điều gì.",
        ],
        "flashcard": {
            "card_id": "FC_PRIZE_01",
            "title": "Quà thật không bao giờ thu phí trước",
            "tip": "Nếu phải trả tiền mới được nhận thưởng thì đó không phải phần thưởng, đó là lừa đảo.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_PRIZE_01",
                "question": "Tin nhắn báo em trúng một chiếc xe đạp điện, chỉ cần đóng 300k phí vận chuyển. Em sẽ?",
                "options": [
                    {"id": "A", "text": "Đóng phí vì phần thưởng đáng giá hơn nhiều"},
                    {"id": "B", "text": "Không đóng, vì trúng thưởng thật không thu phí trước"},
                    {"id": "C", "text": "Nhờ bạn đóng hộ rồi chia đôi phần thưởng"},
                ],
                "correct_option": "B",
                "explanation": "Đây là bẫy 'phí ứng trước'. Nộp xong, kẻ lừa đảo sẽ biến mất.",
            },
            {
                "quiz_id": "QZ_PRIZE_02",
                "question": "Vì sao tin nhắn trúng thưởng thường kèm link rút gọn (bit.ly, ...)?",
                "options": [
                    {"id": "A", "text": "Cho gọn tin nhắn, tiết kiệm ký tự"},
                    {"id": "B", "text": "Để che giấu địa chỉ web thật, tránh bị nghi ngờ"},
                    {"id": "C", "text": "Vì trang web chính thức luôn dùng link rút gọn"},
                ],
                "correct_option": "B",
                "explanation": "Link rút gọn giấu đi tên miền thật, nên em không biết mình sắp vào trang nào.",
            },
        ],
    },
    CATEGORY_OTP_PHISHING: {
        "primary_warning": "TUYỆT ĐỐI KHÔNG gửi mã OTP hay mật khẩu cho bất kỳ ai.",
        "steps": [
            "1. Không gửi mã OTP, mật khẩu cho bất kỳ ai, kể cả người xưng là người quen.",
            "2. Không đăng nhập tài khoản trên các trang web lạ.",
            "3. Đổi mật khẩu ngay nếu em đã lỡ nhập vào trang lạ.",
            "4. Bật xác thực 2 lớp và báo cho bố mẹ biết.",
        ],
        "flashcard": {
            "card_id": "FC_OTP_01",
            "title": "OTP là chìa khóa nhà của em",
            "tip": "Mã OTP chỉ dành riêng cho em, có hiệu lực vài phút. Đưa OTP cho người khác giống như đưa chìa khóa nhà cho kẻ trộm.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_OTP_01",
                "question": "Mã OTP dùng để làm gì và có nên gửi cho người khác không?",
                "options": [
                    {"id": "A", "text": "Là mật khẩu dùng chung, gửi cho ai cũng được"},
                    {"id": "B", "text": "Là mã bảo mật cá nhân quan trọng, tuyệt đối không gửi cho ai"},
                    {"id": "C", "text": "Gửi mã để được nhận quà game"},
                ],
                "correct_option": "B",
                "explanation": "OTP xác nhận danh tính của em. Ai có OTP là chiếm được tài khoản của em ngay lập tức.",
            },
            {
                "quiz_id": "QZ_OTP_02",
                "question": "Em lỡ nhập mật khẩu Facebook vào một trang web lạ. Việc cần làm đầu tiên là gì?",
                "options": [
                    {"id": "A", "text": "Đổi mật khẩu ngay và báo cho bố mẹ"},
                    {"id": "B", "text": "Chờ xem có chuyện gì xảy ra không"},
                    {"id": "C", "text": "Xóa ứng dụng Facebook là xong"},
                ],
                "correct_option": "A",
                "explanation": "Đổi mật khẩu càng sớm càng tốt sẽ chặn kẻ xấu trước khi chúng kịp dùng tài khoản của em.",
            },
        ],
    },
    CATEGORY_ACCOUNT_THREAT: {
        "primary_warning": "KHÔNG sợ hãi, KHÔNG chuyển tiền, BÁO NGƯỜI LỚN ngay lập tức.",
        "steps": [
            "1. Không trả lời, không chuyển tiền dù bị dọa thế nào.",
            "2. Chụp màn hình toàn bộ đoạn tin nhắn làm bằng chứng.",
            "3. Chặn và báo cáo tài khoản đó.",
            "4. Kể ngay với bố mẹ, thầy cô; nếu bị đe dọa nghiêm trọng, người lớn sẽ báo công an.",
        ],
        "flashcard": {
            "card_id": "FC_THREAT_01",
            "title": "Bị đe dọa không phải lỗi của em",
            "tip": "Kẻ xấu dọa để em im lặng. Nói ra với người lớn là cách duy nhất làm chúng mất vũ khí.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_THREAT_01",
                "question": "Một người lạ dọa sẽ tung ảnh của em lên mạng nếu không chuyển 500k. Em nên?",
                "options": [
                    {"id": "A", "text": "Chuyển tiền cho yên chuyện"},
                    {"id": "B", "text": "Im lặng, tự giải quyết một mình"},
                    {"id": "C", "text": "Lưu bằng chứng, chặn tài khoản và báo ngay cho bố mẹ/thầy cô"},
                ],
                "correct_option": "C",
                "explanation": "Chuyển tiền chỉ khiến chúng đòi thêm. Người lớn và công an có cách xử lý kẻ tống tiền.",
            },
            {
                "quiz_id": "QZ_THREAT_02",
                "question": "Tin nhắn báo 'tài khoản của bạn sẽ bị khóa, xác minh ngay tại link này'. Đây là gì?",
                "options": [
                    {"id": "A", "text": "Thông báo thật, cần làm ngay"},
                    {"id": "B", "text": "Chiêu dọa để em hoảng sợ mà bấm vào link giả mạo"},
                    {"id": "C", "text": "Tin nhắn quảng cáo bình thường"},
                ],
                "correct_option": "B",
                "explanation": "Dọa khóa tài khoản là cách khiến em hành động vội vàng. Hãy kiểm tra trong ứng dụng chính thức, không bấm link.",
            },
        ],
    },
    CATEGORY_PHISHING_LINK: {
        "primary_warning": "KHÔNG bấm vào đường link lạ trong tin nhắn.",
        "steps": [
            "1. Không bấm vào link, không đăng nhập bất cứ thông tin gì.",
            "2. Quan sát tên miền: các đuôi lạ như .vip, .xyz, .top thường là trang giả.",
            "3. Nếu cần truy cập, hãy tự gõ địa chỉ chính thức của trang web.",
            "4. Hỏi ý kiến bố mẹ hoặc thầy cô trước khi mở link không rõ nguồn gốc.",
        ],
        "flashcard": {
            "card_id": "FC_LINK_01",
            "title": "Đọc tên miền trước khi bấm",
            "tip": "Trang thật có tên miền quen thuộc (facebook.com, roblox.com). Trang giả hay thêm chữ lạ hoặc đuôi .vip, .xyz, .top.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_LINK_01",
                "question": "Địa chỉ nào dưới đây đáng ngờ nhất?",
                "options": [
                    {"id": "A", "text": "https://www.roblox.com"},
                    {"id": "B", "text": "http://roblox-tangrobux.vip"},
                    {"id": "C", "text": "https://hocmai.vn"},
                ],
                "correct_option": "B",
                "explanation": "Tên miền nhái thương hiệu cộng đuôi .vip là dấu hiệu rõ ràng của trang giả mạo.",
            },
            {
                "quiz_id": "QZ_LINK_02",
                "question": "Trước khi bấm vào một link lạ, việc nên làm là gì?",
                "options": [
                    {"id": "A", "text": "Bấm thử, thấy lạ thì thoát ra"},
                    {"id": "B", "text": "Dừng lại, đọc kỹ tên miền và hỏi người lớn"},
                    {"id": "C", "text": "Gửi cho bạn bấm thử trước"},
                ],
                "correct_option": "B",
                "explanation": "Chỉ cần bấm vào là trang giả đã có cơ hội lừa em nhập mật khẩu. Hỏi người lớn luôn an toàn hơn.",
            },
        ],
    },
    CATEGORY_JOB_SCAM: {
        "primary_warning": "KHÔNG tham gia 'việc nhẹ lương cao', KHÔNG nộp tiền đặt cọc.",
        "steps": [
            "1. Không nhận làm 'nhiệm vụ' online kiếm tiền cho người lạ.",
            "2. Không chuyển khoản đặt cọc dù được hứa hoàn lại.",
            "3. Không cung cấp thông tin cá nhân, ảnh thẻ học sinh, căn cước của bố mẹ.",
            "4. Trao đổi với bố mẹ nếu em muốn làm thêm kiếm tiền tiêu vặt.",
        ],
        "flashcard": {
            "card_id": "FC_JOB_01",
            "title": "Việc nhẹ lương cao = bẫy",
            "tip": "Không có công việc nào trả vài trăm nghìn mỗi ngày cho học sinh chỉ để 'like dạo' hay 'chốt đơn'.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_JOB_01",
                "question": "'Tuyển học sinh làm nhiệm vụ online, 500k/ngày, đặt cọc 200k' — vấn đề nằm ở đâu?",
                "options": [
                    {"id": "A", "text": "Lương hơi thấp so với công sức"},
                    {"id": "B", "text": "Bắt đặt cọc trước là dấu hiệu lừa đảo"},
                    {"id": "C", "text": "Không có gì đáng ngại"},
                ],
                "correct_option": "B",
                "explanation": "Việc làm thật không bao giờ bắt người lao động nộp tiền trước.",
            },
            {
                "quiz_id": "QZ_JOB_02",
                "question": "Khi muốn kiếm tiền tiêu vặt, cách an toàn nhất với học sinh THCS là gì?",
                "options": [
                    {"id": "A", "text": "Trao đổi với bố mẹ và chọn việc phù hợp, có người lớn biết"},
                    {"id": "B", "text": "Nhận việc online từ người lạ trên mạng"},
                    {"id": "C", "text": "Vay tiền bạn để đầu tư trước"},
                ],
                "correct_option": "A",
                "explanation": "Có người lớn đồng hành là lớp bảo vệ tốt nhất trước các lời mời trên mạng.",
            },
        ],
    },
    CATEGORY_GAMBLING: {
        "primary_warning": "KHÔNG nạp tiền, KHÔNG tham gia — cờ bạc online là bẫy và là vi phạm pháp luật.",
        "steps": [
            "1. Không bấm link, không đăng ký tài khoản, không nạp bất kỳ khoản tiền nào.",
            "2. Chặn và xóa tin nhắn, báo cáo số gửi tin.",
            "3. Nhớ rằng người dưới 18 tuổi tham gia cá cược là vi phạm pháp luật.",
            "4. Kể với bố mẹ nếu em đã lỡ nạp tiền — càng giấu càng mất nhiều.",
        ],
        "flashcard": {
            "card_id": "FC_GAMB_01",
            "title": "'Tân thủ nhận lộc' là mồi nhử",
            "tip": "Các trang cờ bạc luôn cho người mới thắng vài lần đầu để em nạp thêm, rồi lấy sạch. Không có 'tiền dễ' trên mạng.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_GAMB_01",
                "question": "Tin nhắn mời 'nạp đầu nhận gấp đôi, tân thủ nhận ngay 500k' nói lên điều gì?",
                "options": [
                    {"id": "A", "text": "Một chương trình khuyến mãi bình thường"},
                    {"id": "B", "text": "Mồi nhử của trang cờ bạc để em nạp tiền vào"},
                    {"id": "C", "text": "Cơ hội kiếm tiền tiêu vặt nhanh"},
                ],
                "correct_option": "B",
                "explanation": "Đây là kịch bản quen thuộc của cờ bạc online: cho thắng nhỏ lúc đầu, sau đó em sẽ mất toàn bộ số tiền đã nạp.",
            },
        ],
    },
    CATEGORY_SUSPICIOUS_INVITE: {
        "primary_warning": "Hãy tìm hiểu kỹ trước khi tham gia nhóm lạ.",
        "steps": [
            "1. Tìm hiểu ai là người quản lý nhóm, nhóm để làm gì.",
            "2. Không cung cấp thông tin cá nhân, ảnh, trường lớp trong nhóm lạ.",
            "3. Hỏi ý kiến bố mẹ hoặc thầy cô trước khi tham gia.",
            "4. Rời nhóm ngay nếu thấy nội dung xấu hoặc có người hỏi tiền, hỏi tài khoản.",
        ],
        "flashcard": {
            "card_id": "FC_INVITE_01",
            "title": "Nhóm lạ - cửa ngõ của người lạ",
            "tip": "Trong nhóm chat lạ, người xấu có thể tiếp cận và làm quen với em. Chỉ tham gia nhóm do thầy cô, bạn bè thật lập ra.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_INVITE_01",
                "question": "Một người lạ mời em vào nhóm chat 'học sinh vui vẻ' qua link. Em nên?",
                "options": [
                    {"id": "A", "text": "Vào ngay cho vui"},
                    {"id": "B", "text": "Tìm hiểu nhóm của ai, hỏi ý kiến người lớn rồi mới quyết định"},
                    {"id": "C", "text": "Vào rồi mời thêm bạn bè cùng lớp"},
                ],
                "correct_option": "B",
                "explanation": "Nhóm lạ là nơi người xấu dễ tiếp cận học sinh nhất. Hỏi người lớn trước là an toàn nhất.",
            },
            {
                "quiz_id": "QZ_INVITE_02",
                "question": "Trong nhóm chat lạ, thông tin nào em KHÔNG nên chia sẻ?",
                "options": [
                    {"id": "A", "text": "Tên trường, lớp, số điện thoại, ảnh cá nhân"},
                    {"id": "B", "text": "Ý kiến về một bộ phim"},
                    {"id": "C", "text": "Một câu chào hỏi"},
                ],
                "correct_option": "A",
                "explanation": "Thông tin cá nhân giúp kẻ xấu dựng lên những lời lừa đảo nghe rất thật.",
            },
        ],
    },
    CATEGORY_ADS_SPAM: {
        "primary_warning": "Chưa thấy dấu hiệu lừa tiền, nhưng em không nên bấm link quảng cáo lạ.",
        "steps": [
            "1. Không bấm link, không để lại số điện thoại hay địa chỉ.",
            "2. Không đặt hàng khi chưa hỏi ý kiến bố mẹ.",
            "3. Chặn số nếu tin nhắn quảng cáo gửi liên tục.",
        ],
        "flashcard": {
            "card_id": "FC_ADS_01",
            "title": "Quảng cáo lạ - đừng vội để lại thông tin",
            "tip": "Số điện thoại và địa chỉ của em là thông tin riêng tư. Đừng để lại trên các trang quảng cáo không rõ nguồn gốc.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_ADS_01",
                "question": "Nhận tin quảng cáo giảm giá 90% từ số lạ, em nên làm gì?",
                "options": [
                    {"id": "A", "text": "Bấm link xem thử ngay"},
                    {"id": "B", "text": "Bỏ qua hoặc hỏi bố mẹ, không để lại thông tin cá nhân"},
                    {"id": "C", "text": "Gửi số điện thoại để được tư vấn"},
                ],
                "correct_option": "B",
                "explanation": "Giảm giá phi lý thường là mồi nhử. Không để lại thông tin là cách tự bảo vệ đơn giản nhất.",
            },
        ],
    },
    # Dung khi mo hinh ML thay dang ngo nhung bo luat chua tim duoc bang chung cu the.
    "GENERIC_CAUTION": {
        "primary_warning": "HÃY CẨN THẬN: chưa xác định rõ tin nhắn này có an toàn hay không.",
        "steps": [
            "1. Chưa làm theo bất cứ yêu cầu nào trong tin nhắn.",
            "2. Kiểm tra xem người gửi có đúng là người em quen không (gọi điện trực tiếp).",
            "3. Tuyệt đối không gửi tiền, mã OTP, mật khẩu hay thông tin cá nhân.",
            "4. Cho bố mẹ hoặc thầy cô xem tin nhắn này để cùng kiểm chứng.",
        ],
        "flashcard": {
            "card_id": "FC_GEN_01",
            "title": "Không chắc chắn thì hỏi người lớn",
            "tip": "Khi một tin nhắn làm em thấy lăn tăn, đó đã là lý do đủ để dừng lại và hỏi bố mẹ hoặc thầy cô.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_GEN_01",
                "question": "Khi nhận một tin nhắn lạ mà em không chắc có an toàn không, bước đầu tiên nên làm là gì?",
                "options": [
                    {"id": "A", "text": "Làm theo trước, sai thì sửa sau"},
                    {"id": "B", "text": "Dừng lại, không làm theo và hỏi người lớn"},
                    {"id": "C", "text": "Chuyển tiếp cho bạn bè xem thử"},
                ],
                "correct_option": "B",
                "explanation": "Dừng lại và hỏi người lớn là bước an toàn nhất, kể cả khi cuối cùng tin nhắn đó vô hại.",
            },
        ],
    },
    CATEGORY_SAFE: {
        "primary_warning": "Tin nhắn này có vẻ bình thường. Em vẫn nên giữ thói quen cảnh giác.",
        "steps": [
            "1. Tiếp tục trao đổi bình thường.",
            "2. Nếu sau đó có ai hỏi tiền, mã OTP hay mật khẩu, hãy dừng lại và kiểm tra lại.",
            "3. Không chia sẻ thông tin cá nhân với người chưa gặp ngoài đời.",
        ],
        "flashcard": {
            "card_id": "FC_SAFE_01",
            "title": "3 câu hỏi vàng trước khi làm theo tin nhắn",
            "tip": "Ai gửi? Họ muốn gì (tiền, mã, mật khẩu)? Có hối thúc không? Chỉ cần một câu trả lời đáng ngờ là phải hỏi người lớn.",
        },
        "quizzes": [
            {
                "quiz_id": "QZ_SAFE_01",
                "question": "Dấu hiệu nào sau đây thường xuất hiện trong tin nhắn lừa đảo?",
                "options": [
                    {"id": "A", "text": "Hỏi bài tập về nhà"},
                    {"id": "B", "text": "Hối thúc gấp gáp và yêu cầu tiền, mã OTP hoặc mật khẩu"},
                    {"id": "C", "text": "Nhắc lịch trực nhật"},
                ],
                "correct_option": "B",
                "explanation": "Gấp gáp + đòi tiền/mã là công thức chung của hầu hết tin nhắn lừa đảo.",
            },
            {
                "quiz_id": "QZ_SAFE_02",
                "question": "Khi không chắc một tin nhắn có an toàn hay không, em nên?",
                "options": [
                    {"id": "A", "text": "Hỏi bố mẹ hoặc thầy cô trước khi làm theo"},
                    {"id": "B", "text": "Cứ làm theo rồi tính sau"},
                    {"id": "C", "text": "Chuyển tiếp cho các bạn cùng làm"},
                ],
                "correct_option": "A",
                "explanation": "Hỏi người lớn không bao giờ là thừa. Một phút hỏi han tránh được rất nhiều rắc rối.",
            },
        ],
    },
}
