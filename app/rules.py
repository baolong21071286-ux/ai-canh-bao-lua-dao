"""Bo luat nhan dien dau hieu lua dao (nen tang cua Explainable AI - Module 2).

Moi luat duoc viet bang tieng Viet **khong dau, chu thuong** vi chung se duoc
doi chieu voi ban fold cua tin nhan (xem :mod:`app.text_utils`). Nho do he thong
bat duoc ca tin nhan go tat, khong dau, hoac co dau day du.

Moi luat mang theo `reason` - cau giai thich viet cho hoc sinh THCS doc hieu.
Day chinh la phan "giai thich duoc" ma dac ta yeu cau o Muc 1.2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Tuple

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

# --- Nhom tin hieu (signal) dung cho cac luat ket hop o classifier ---
SIG_IMPERSONATION = "IMPERSONATION"
SIG_MONEY = "MONEY"
SIG_OTP = "OTP"
SIG_THREAT = "THREAT"
SIG_FREEBIE = "FREEBIE"
SIG_PRIZE = "PRIZE"
SIG_LINK = "LINK"
SIG_URGENCY = "URGENCY"
SIG_SECRECY = "SECRECY"
SIG_JOB = "JOB"
SIG_INVITE = "INVITE"
SIG_ADS = "ADS"
SIG_SAFE = "SAFE"


@dataclass(frozen=True)
class Rule:
    """Mot luat nhan dien: bieu thuc chinh quy + trong so + ly do giai thich."""

    id: str
    signal: str
    category: str
    weight: float
    reason: str
    patterns: Tuple[str, ...]
    hard_danger: bool = False
    #: Luat "khuech dai": chi duoc tinh diem khi da co it nhat mot luat rui ro khac
    #: kich hoat (vd: nhac ten game, nhac gia tri phan thuong).
    amplifier: bool = False
    #: Luat du manh de mot minh ket luan "nguy hiem" (khong can tin hieu di kem).
    standalone: bool = False
    compiled: Tuple[Pattern[str], ...] = field(default=(), repr=False, compare=False)

    def __post_init__(self) -> None:  # pragma: no cover - chi bien dich regex
        object.__setattr__(
            self, "compiled", tuple(re.compile(p) for p in self.patterns)
        )


def _r(*args, **kwargs) -> Rule:
    return Rule(*args, **kwargs)


# ---------------------------------------------------------------------------
# 1. MAO DANH (thay co, nguoi than, ban be)
# ---------------------------------------------------------------------------
IMPERSONATION_RULES: List[Rule] = [
    _r(
        id="IMP_TEACHER_SELF_INTRO",
        signal=SIG_IMPERSONATION,
        category=CATEGORY_IMPERSONATION_TEACHER,
        weight=0.45,
        reason="Dấu hiệu mạo danh thầy cô quen biết (tự xưng là thầy/cô rồi nhắn riêng).",
        patterns=(
            r"\b(thay|co)\s+[a-z]{1,12}\s+(the duc|toan|van|anh|ly|hoa|sinh|su|dia|tin|chu nhiem|bo mon)?\s*(day|day nhe|day em|day con)\b",
            r"\b(day la|toi la|minh la|to la|em oi day la)\s+(thay|co|giao vien|hieu truong)\b",
            r"\b(thay|co)\s+(chu nhiem|bo mon|hieu truong|tong phu trach)\s+(day|nhan|thong bao|can)\b",
            r"\b(thay|co)\s+giao\s+day\b",
        ),
    ),
    _r(
        id="IMP_SCHOOL_NOTICE",
        signal=SIG_IMPERSONATION,
        category=CATEGORY_IMPERSONATION_TEACHER,
        weight=0.35,
        reason="Giả danh thông báo của nhà trường để tạo lòng tin.",
        patterns=(
            r"\b(nha truong|ban giam hieu|phong dao tao|hoi phu huynh)\s+(thong bao|yeu cau|can|de nghi|gui)\b",
            r"\bthong bao (khan|gap) (cua )?(nha truong|lop)\b",
            r"\b(toi|minh|chi|anh|em)\s+la\s+(tro ly|thu ky|nguoi quen|dong nghiep|ban|nguoi nha|phu huynh)\s+(cua\s+)?(thay|co|nha truong|lop)\b",
            r"\b(thay|co)\s+(nho|bao|nhan)\s+(minh|toi|chi|anh)\s+(nhan|nhac|bao)\s+(em|cac em|con)\b",
        ),
    ),
    _r(
        id="IMP_RELATIVE_SELF_INTRO",
        signal=SIG_IMPERSONATION,
        category=CATEGORY_IMPERSONATION_RELATIVE,
        weight=0.4,
        reason="Tự xưng là bố mẹ/người thân nhưng nhắn từ tài khoản lạ.",
        patterns=(
            r"\b(me|bo|ba|di|chu|bac|cau|mo|anh hai|chi hai)\s+(day|đay|day con|day nhe)\b",
            r"\b(day la|toi la|minh la)\s+(me|bo|ba|di|chu|bac|phu huynh)\s+(cua )?(con|em|chau)?\b",
            r"\bme (doi|dang dung|moi doi) (so|may|dien thoai) (moi|khac)\b",
        ),
    ),
    _r(
        id="IMP_FRIEND_NEW_ACCOUNT",
        signal=SIG_IMPERSONATION,
        category=CATEGORY_IMPERSONATION_RELATIVE,
        weight=0.38,
        reason="Bạn bè 'đổi nick' rồi hỏi vay tiền là chiêu chiếm tài khoản rất phổ biến.",
        patterns=(
            r"\b(minh|to|tao|tui)\s+(la|day)\s+[a-z]{1,12}\s+(ban|bn|hoc)\s*(cung|chung)?\s*(lop|truong)?\b",
            r"\b(nick|acc|facebook|zalo|fb)\s+(cu|chinh)\s+(cua )?(minh|to|tao)\s+(bi|dang bi)\s*(mat|hack|khoa)\b",
            r"\bminh (lap|dung) (nick|acc|tai khoan) (moi|phu)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 2. YEU CAU TIEN / THE CAO
# ---------------------------------------------------------------------------
MONEY_RULES: List[Rule] = [
    _r(
        id="MONEY_TOPUP_HELP",
        signal=SIG_MONEY,
        category=CATEGORY_IMPERSONATION_TEACHER,
        weight=0.5,
        reason="Yêu cầu cung cấp tiền/thẻ cào qua tin nhắn.",
        patterns=(
            r"\bnap\s*(ho|giup|dum|gium)\b",
            r"\b(mua|nap)\s+(gium|giup|ho)\s*\d*\s*(cai\s+)?(the|card)\b",
            r"\b(mua|nap)\s+\d+\s*(cai\s+)?(the|card)\s*(cao|dien thoai|viettel|vina|vinaphone|mobi|mobifone|garena|zing|vtc)\b",
            r"\b\d+\s*(cai\s+)?(the|card)\s*(cao|viettel|vina|vinaphone|mobi|mobifone|garena|zing|vtc)\b",
            r"\b(nap|chuyen|gui)\s+(the|tien)\s+(vao|den|cho)\s+(so|stk|tai khoan|nick|acc)\b",
            r"\b(ma|so seri|seri)\s+(the|card)\b",
            r"\bcao the (gui|chup|nhan)\b",
        ),
    ),
    _r(
        # "nap the", "the cao" xuat hien day ray trong tin khuyen mai HOP LE cua nha mang,
        # nen chi tinh diem khi trong tin da co tin hieu rui ro khac.
        id="MONEY_TOPUP_MENTION",
        signal=SIG_MONEY,
        category=CATEGORY_IMPERSONATION_TEACHER,
        weight=0.3,
        amplifier=True,
        reason="Nhắc tới việc nạp thẻ/thẻ cào — cách chuyển tiền mà kẻ lừa đảo hay yêu cầu.",
        patterns=(
            r"\b(nap|mua)\s+(the|card)\b",
            r"\bthe cao\b",
        ),
    ),
    _r(
        id="MONEY_TRANSFER",
        signal=SIG_MONEY,
        category=CATEGORY_IMPERSONATION_RELATIVE,
        weight=0.45,
        reason="Yêu cầu chuyển tiền / số tài khoản ngân hàng qua tin nhắn.",
        patterns=(
            r"\bchuyen\s+(khoan|tien|gap|ngay)\b",
            r"\b(so|stk)\s*(tai khoan|tk)\b",
            r"\bso tai khoan\b",
            r"\b(cho|cho minh|cho to|cho tao)\s+(muon|vay|mun)\s*(tam|do)?\s*\d",
            r"\b(muon|vay)\s+(tam|gap|nong)\s*\d*\s*(k|nghin|tram|trieu|dong|d)?\b",
            r"\bbank\s*(gium|giup|ho|cho)\b",
        ),
    ),
    _r(
        id="MONEY_ADVANCE_FEE",
        signal=SIG_MONEY,
        category=CATEGORY_FAKE_PRIZE,
        weight=0.52,
        reason="Đòi nộp phí trước khi nhận quà — quà thật không bao giờ bắt trả phí.",
        patterns=(
            r"\b(phi|le phi|chi phi|tien)\s*(van chuyen|ship|giao hang|nhan (qua|thuong|giai)|ho so|kich hoat|xac nhan|thue)\b",
            r"\bnop\s+(truoc|gap)\s+(mot|1)?\s*(khoan|it)?\s*(phi|tien)\b",
        ),
    ),
    _r(
        id="MONEY_PROMISE_REPAY",
        signal=SIG_MONEY,
        category=CATEGORY_IMPERSONATION_RELATIVE,
        weight=0.3,
        amplifier=True,
        reason="Hứa 'mai trả lại' để em yên tâm đưa tiền — lời hứa này gần như không bao giờ được thực hiện.",
        patterns=(
            r"\b(mai|chieu|toi|hom sau|tuan sau)\s+(minh|to|tao|tui|thay|co|me|bo|anh|chi)\s+(tra|gui lai|hoan lai|dua lai)\b",
            r"\b(tra|gui|hoan)\s+(lai\s+)?(cho\s+)?(em|ban|may|con)\s+(sau|ngay|gap doi)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 3. OTP / MAT KHAU
# ---------------------------------------------------------------------------
OTP_RULES: List[Rule] = [
    _r(
        id="OTP_REQUEST",
        signal=SIG_OTP,
        category=CATEGORY_OTP_PHISHING,
        weight=0.75,
        hard_danger=True,
        reason="Đòi mã OTP / mã xác minh — đây là chìa khóa tài khoản, không ai được phép hỏi.",
        patterns=(
            r"\b(nhap|gui|doc|cung cap|cho|bao|chuyen|dien|xac nhan)\s+((minh|to|tao|anh|chi|em|lai|xin|gium|giup|ho)\s+){0,3}(ma\s+)?(otp|ma xac (minh|nhan|thuc)|ma bao mat|ma kich hoat)\b",
            r"\b(ma\s+)?otp\s+(vua|moi|da)\s+(gui|nhan|den)\b",
            r"\bma (xac minh|xac nhan|bao mat)\s+(gom|la|vua)\b",
            r"\bdoc ma (6|sau) so\b",
        ),
    ),
    _r(
        id="OTP_PASSWORD_REQUEST",
        signal=SIG_OTP,
        category=CATEGORY_OTP_PHISHING,
        weight=0.7,
        hard_danger=True,
        reason="Hỏi mật khẩu/tài khoản đăng nhập — người tử tế không bao giờ hỏi điều này.",
        patterns=(
            r"\b(cho|gui|nhap|cung cap|bao|dien|doc)\s+(minh|to|tao|anh|chi|em|lai)?\s*(xin\s+)?(mat khau|pass|password|tai khoan va mat khau)\b",
            r"\bxin\s+(lai\s+)?(mat khau|pass|password)\b",
            r"\bdang nhap\s+(bang|vao)\s+(tai khoan|acc|nick)\s+(facebook|fb|zalo|google|gmail|discord|roblox|garena)\b",
            r"\b(cho|cho anh|cho chi|cho minh|cho to)?\s*(muon|muon tam|xin)\s+(nick|acc|tai khoan)\b",
            r"\b(nick|acc|tai khoan)\s+(cua em|cua ban|cua con)\s+(cho|de)\s+(anh|chi|minh)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 4. DE DOA / CHIEM TAI KHOAN
# ---------------------------------------------------------------------------
THREAT_RULES: List[Rule] = [
    _r(
        id="THREAT_BLACKMAIL",
        signal=SIG_THREAT,
        category=CATEGORY_ACCOUNT_THREAT,
        weight=0.8,
        hard_danger=True,
        reason="Lời đe dọa, tống tiền nhằm làm học sinh hoảng sợ và im lặng làm theo.",
        patterns=(
            r"\b(tung|phat tan|dang|gui|lo|public)\s+(anh|hinh|clip|video|tin nhan)\s*(nong|nhay cam|rieng tu|cua (em|ban|may|con))?\b",
            r"\b(neu\s+)?khong\s+(chuyen|nap|gui|dua|tra|lam theo)\b.{0,40}?\b(se|thi)\b.{0,30}?\b(tung|phat tan|dang|bao|khoa|xoa|cho ca truong|noi voi)\b",
            r"\btung\s+(len|vao)\s+(group|nhom|mang|fb|facebook|lop|truong)\b",
            r"\b(dung|cho)\s+trach\b",
            r"\b(gui|cho|dua|show)\s+(het\s+)?(anh|hinh|clip|video|screenshot|anh chup)\b.{0,40}?\b(ca lop|ca truong|moi nguoi|len nhom|cho bo me)\b",
            r"\bkhong\s+(gui|chuyen|nap|dua)\s+\d+\s*(k|nghin|tram|trieu|tr)\b.{0,40}?\b(thi|se)\b",
            r"\b(tao|anh|chung toi)\s+(se|sap)\s+(cho|de)?\s*(ca (lop|truong)|moi nguoi)\s+(biet|xem)\b",
            r"\b(to cao|kien|bao cong an)\s+.{0,20}\bneu (khong|em khong)\b",
        ),
    ),
    _r(
        id="THREAT_ACCOUNT_LOCK",
        signal=SIG_THREAT,
        category=CATEGORY_ACCOUNT_THREAT,
        weight=0.55,
        reason="Dọa khóa/mất tài khoản để ép học sinh bấm link hoặc khai thông tin.",
        patterns=(
            r"\b(tai khoan|nick|acc|thue bao|dich vu)\b.{0,40}?\b(se|sap|dang|bi)\s*(bi\s+)?(khoa|xoa|vo hieu hoa|dinh chi|hack|tam ngung|ngung|han che|phong toa|tru tien)\b",
            r"\b(tai khoan|nick|acc)\b.{0,30}?\bbi\s+(dang nhap|truy cap|xam nhap)\s*(la)?\b",
            r"\b(nick|acc|tai khoan)\b.{0,20}?\b(dang\s+)?(trong tay|do tao giu)\b",
            r"\bmuon lay lai\s+(thi|phai)\b",
            r"\bhack\s+(nick|acc|tai khoan|fb|zalo)\b",
            r"\b(canh bao|thong bao)\s+(bao mat|dang nhap la)\b",
            r"\bxac minh (ngay|gap)?\s*(de|neu khong)\s+(tranh|se)\s+(mat|khoa)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 5. QUA TANG / VAT PHAM GAME MIEN PHI
# ---------------------------------------------------------------------------
FREEBIE_RULES: List[Rule] = [
    _r(
        id="FREEBIE_GAME_ITEM",
        signal=SIG_FREEBIE,
        category=CATEGORY_GAME_TOPUP,
        weight=0.5,
        reason="Hứa tặng vật phẩm/kim cương/Robux miễn phí — mồi nhử quen thuộc với học sinh.",
        patterns=(
            r"\b(mien phi|free|tang|nhan|hack|share)\s*\d*\s*(robux|kim cuong|kc|quan huy|qh|vang|xu|skin|vat pham|nick vip|acc vip|sung|tuong|uc)\b",
            r"\b(robux|kim cuong|quan huy|skin|vat pham|nick|acc)\s+(mien phi|free|tang|khuyen mai|tri an)\b",
            r"\b(su kien|event)\s+(tri an|tang qua|mien phi)\s*(game|roblox|lien quan|free fire|ff|play together)?\b",
            r"\bnap 1 (tang|duoc) \d+\b",
            r"\b(hack|bug|tool)\s+(kim cuong|robux|quan huy|game)\b",
        ),
    ),
    _r(
        id="FREEBIE_GAME_BRAND",
        signal=SIG_FREEBIE,
        category=CATEGORY_GAME_TOPUP,
        weight=0.18,
        reason="Nhắc tới game phổ biến của lứa tuổi học sinh để tạo sự tin tưởng.",
        amplifier=True,
        patterns=(
            r"\b(roblox|robux|lien quan|lienquan|free fire|freefire|ff|play together|among us|pubg|garena|toca boca|blox fruit|minecraft)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 6. TRUNG THUONG GIA
# ---------------------------------------------------------------------------
PRIZE_RULES: List[Rule] = [
    _r(
        id="PRIZE_WIN_ANNOUNCE",
        signal=SIG_PRIZE,
        category=CATEGORY_FAKE_PRIZE,
        weight=0.55,
        reason="Thông báo trúng thưởng dù em chưa hề tham gia chương trình nào.",
        patterns=(
            r"\b(chuc mung|thong bao)\s+.{0,30}\b(da )?(trung|nhan duoc|duoc chon)\b",
            r"\btrung\s+(thuong|giai|dac biet|mot|1|\d)\b",
            r"\b(ban|em|so dien thoai cua ban)\s+(la|da)\s+(nguoi|khach hang)?\s*(may man|duoc chon)\b",
            r"\b(phan thuong|giai thuong)\s+(cua ban|la|gom)\b",
        ),
    ),
    _r(
        id="PRIZE_HIGH_VALUE_ITEM",
        signal=SIG_PRIZE,
        category=CATEGORY_FAKE_PRIZE,
        weight=0.2,
        reason="Hứa hẹn phần thưởng giá trị lớn để đánh vào lòng tham.",
        amplifier=True,
        patterns=(
            r"\b(iphone|ipad|airpod|macbook|xe dap dien|xe may|laptop|may tinh bang)\s*\d*\s*(pro|max|plus|vinfast)?\b",
            r"\b\d+\s*(trieu|tr)\s*(dong|d)?\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 7. LINK LA / TRANG GIA MAO
# ---------------------------------------------------------------------------
PHISHING_LINK_RULES: List[Rule] = [
    # Luu y: viec cham diem TEN MIEN da chuyen sang app/link_analyzer.py de doi chieu
    # voi danh sach trang chinh thong. O day chi giu cac luat dua tren *cach hanh van*.
    _r(
        id="LINK_CLICK_CALL",
        signal=SIG_LINK,
        category=CATEGORY_PHISHING_LINK,
        weight=0.3,
        reason="Hối thúc bấm vào liên kết để 'nhận' hoặc 'xác nhận' điều gì đó.",
        patterns=(
            r"\b(click|bam|an|truy cap|vao|dang nhap)\s+(ngay\s+)?(vao\s+)?(link|duong link|duong dan|day|dia chi|web|trang)\b",
            r"\blink (duoi day|sau day|sau|nay)\b",
        ),
    ),
    _r(
        id="PHISH_LOGIN_ALERT",
        signal=SIG_THREAT,
        category=CATEGORY_ACCOUNT_THREAT,
        weight=0.5,
        reason="Báo 'tài khoản bị đăng nhập lạ / giao dịch bất thường' rồi bắt bấm link — chiêu lừa ngân hàng phổ biến nhất.",
        patterns=(
            r"\b(dang nhap|truy cap|giao dich|tieu dung)\b.{0,30}?\b(tren\s+)?(thiet bi|vung|dia diem|noi)\s*(khac|la|bat thuong|nuoc ngoai)\b",
            r"\bphat hien\b.{0,40}?\b(bat thuong|dang nhap la|truy cap la)\b",
            r"\b(neu khong phai|neu day khong phai)\s+(ban|quy khach|anh|chi)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 7b. DU NAP TIEN CO BAC / KIEM TIEN NHANH (rut ra tu du lieu SMS that)
# ---------------------------------------------------------------------------
GAMBLING_RULES: List[Rule] = [
    _r(
        id="GAMBLING_QUICK_MONEY",
        signal=SIG_JOB,
        category=CATEGORY_GAMBLING,
        weight=0.6,
        reason="Dụ nạp tiền vào trang cờ bạc/đổi thưởng bằng lời hứa 'tân thủ nhận lộc', 'nạp đầu nhân đôi'.",
        patterns=(
            r"\b(nap dau|tan thu|tan binh|hoi vien moi)\b",
            r"\b(nhan|tang)\s+(ngay\s+)?(loc|von|thuong)\b.{0,20}?\b(dang ky|nap|tai khoan moi)\b",
            r"\b(no hu|game bai|ca cuoc|soi cau|lo de|xoc dia|ban ca|tai xiu|casino|keo nha cai)\b",
            r"\b(nap|dat)\s+.{0,15}\b(nhan|an)\s+(gap|x)\s*\d\b",
            r"\b(rut tien|doi thuong)\s+(nhanh|24/7|uy tin)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 8. VIEC NHE LUONG CAO
# ---------------------------------------------------------------------------
JOB_RULES: List[Rule] = [
    _r(
        id="JOB_EASY_MONEY",
        signal=SIG_JOB,
        category=CATEGORY_JOB_SCAM,
        weight=0.6,
        reason="Dụ 'việc nhẹ lương cao' — bẫy lừa đảo nhắm vào học sinh muốn kiếm tiền tiêu vặt.",
        patterns=(
            r"\bviec (nhe|lam them)\s+.{0,15}\bluong cao\b",
            r"\b(lam nhiem vu|chot don|like dao|thuc don)\s+.{0,20}\b(kiem|nhan|huong)\s+(tien|hoa hong|\d)\b",
            r"\b(tuyen|can tuyen)\s+(ctv|cong tac vien|nguoi lam|hoc sinh|sinh vien)\s*(online|tai nha)?\b",
            r"\bkiem\s+\d+\s*(k|tram|trieu)\s*(\/|mot|1)?\s*(ngay|buoi|gio)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 9. THUC GIUC / BI MAT (khong tu quyet dinh nhan nhung khuech dai rui ro)
# ---------------------------------------------------------------------------
PRESSURE_RULES: List[Rule] = [
    _r(
        id="URGENCY_TIME_PRESSURE",
        signal=SIG_URGENCY,
        category=CATEGORY_SAFE,
        weight=0.22,
        reason="Tạo áp lực thời gian để học sinh không kịp suy nghĩ.",
        amplifier=True,
        patterns=(
            r"\b(gap|gap lam|gap qua)\b",
            r"\b(nhanh len|ngay lap tuc|lien|lien tay|khan cap|khan truong)\b",
            r"\b(trong|con)\s+\d+\s*(phut|gio|tieng|ngay)\s*(nua|thoi)?\b",
            r"\b(het han|sap het|han chot|chi con hom nay|duy nhat hom nay|so luong co han)\b",
            r"\b(lam ngay|tra loi ngay|xac nhan ngay|bam ngay|nap ngay|chuyen ngay)\b",
        ),
    ),
    _r(
        id="SECRECY_KEEP_QUIET",
        signal=SIG_SECRECY,
        category=CATEGORY_SAFE,
        weight=0.45,
        reason="Bắt giữ bí mật, không cho nói với bố mẹ — dấu hiệu lừa đảo rất rõ ràng.",
        patterns=(
            r"\b(dung|khong duoc|dung co|nho dung)\s+(noi|ke|bao|cho)\s+(voi\s+)?(bo me|ba me|gia dinh|nguoi lon|thay co|ai)\b",
            r"\b(giu|la)\s+(bi mat|chuyen nay bi mat)\b",
            r"\b(xoa|delete)\s+(tin nhan|doan chat)\s+(nay|sau khi)\b",
            r"\bchi (minh|hai) (em|con) (voi|va) (anh|chi|thay|co) (biet|thoi)\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 10. NGHI VAN MUC THAP: moi nhom la, quang cao
# ---------------------------------------------------------------------------
LOW_RISK_RULES: List[Rule] = [
    _r(
        id="INVITE_UNKNOWN_GROUP",
        signal=SIG_INVITE,
        category=CATEGORY_SUSPICIOUS_INVITE,
        weight=0.3,
        reason="Lời mời vào nhóm lạ chưa rõ mục đích, người lạ có thể tiếp cận em trong đó.",
        patterns=(
            r"\b(vao|tham gia|join)\s+(nhom|group|box|server)\s*(nay|kin|vip|zalo|tele|telegram|discord)?\b",
            r"\bmoi (ban|em|cau)\s+(vao|tham gia)\b",
            r"\b(nhom|group)\s+(kin|vip|bi mat|18|hoc sinh vui ve)\b",
            r"\b(nhom|group|box)\s+(chat\s+)?(moi|la)\b",
        ),
    ),
    _r(
        id="ADS_DIRECT_OFFER",
        signal=SIG_ADS,
        category=CATEGORY_ADS_SPAM,
        weight=0.3,
        reason="Tin chào hàng gửi thẳng tới số máy cá nhân, chưa rõ người bán là ai.",
        patterns=(
            r"\b(inbox|ib|nhan tin|lien he)\s+(de|ngay|minh|shop)?\s*(dat hang|tu van|nhan gia|lay gia|bao gia)\b",
            r"\b(san pham|hang|order|dat hang|giay|ao|balo|phu kien)\b.{0,25}?\b(gia chi|chi tu|gia re|sale)\b",
            r"\b(xa kho|thanh ly|so luong co han)\b",
        ),
    ),
    _r(
        id="ADS_PROMO_WORDS",
        signal=SIG_ADS,
        category=CATEGORY_ADS_SPAM,
        weight=0.22,
        amplifier=True,
        reason="Dùng từ ngữ khuyến mãi để thu hút sự chú ý.",
        patterns=(
            r"\b(sale|giam gia|khuyen mai|khuyen mai soc|uu dai|flash sale)\s*(soc|khung|\d+%)?\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# 11. TIN HIEU AN TOAN (keo diem rui ro xuong)
# ---------------------------------------------------------------------------
SAFE_RULES: List[Rule] = [
    _r(
        id="SAFE_SCHOOLWORK",
        signal=SIG_SAFE,
        category=CATEGORY_SAFE,
        weight=0.3,
        reason="Nội dung trao đổi bài vở, sinh hoạt lớp bình thường.",
        patterns=(
            r"\b(bai tap|bai ve nha|bai kiem tra|de cuong|on thi|on tap|kiem tra 15 phut|kiem tra mieng|thi hoc ki)\b",
            r"\b(truc nhat|sinh hoat lop|chao co|lao dong|hoc nhom|hop lop|di hoc|nghi hoc|tiet hoc)\b",
            r"\b(chep bai|muon vo|muon sach|nop bai|lam bai|giai bai|bai\s+\d+\s+trang\s+\d+)\b",
            r"\b(sgk|vo bai tap|sach giao khoa|thoi khoa bieu|lich hoc|dong phuc)\b",
            r"\b(quy lop|tien (xe|quy|an|nuoc|ghe)|tham quan|da ngoai|hoi phu huynh)\b.{0,40}?\b(lop truong|thu quy|co chu nhiem|nop cho)\b",
        ),
    ),
    _r(
        id="SAFE_FAMILY_DAILY",
        signal=SIG_SAFE,
        category=CATEGORY_SAFE,
        weight=0.25,
        reason="Tin nhắn sinh hoạt gia đình/bạn bè thường ngày.",
        patterns=(
            r"\b(me|bo|ba)\s+(don|nau|de|mua|dang|sap)\s+(com|com trua|com toi|o cong|xong)\b",
            r"\b(an com|ve som|ve nha|di ngu|nho khoa cua|mang ao mua|troi mua)\b",
            r"\b(chuc|chuc mung)\s+(ngu ngon|sinh nhat|nam moi|ngay 20-11|20 11)\b",
            r"\b(mai (minh|to|tui) (di|den)|di da cau|di da bong|ra san|hen gap)\b",
        ),
    ),
]

DOWNLOAD_RULES: List[Rule] = [
    _r(
        id="LINK_APK_DOWNLOAD",
        signal=SIG_LINK,
        category=CATEGORY_PHISHING_LINK,
        weight=0.55,
        reason="Rủ tải file cài đặt lạ (.apk/.exe) — đây thường là phần mềm theo dõi hoặc chiếm tài khoản.",
        standalone=True,
        patterns=(
            r"\b(tai|cai|download)\s*(ve|dat|file|ung dung|app)?\b[^\s]*\.(apk|exe|zip|rar)\b",
        ),
    ),
]

PII_RULES: List[Rule] = [
    _r(
        id="PII_CONTACT_REQUEST",
        signal=SIG_INVITE,
        category=CATEGORY_SUSPICIOUS_INVITE,
        weight=0.35,
        reason="Đề nghị để lại thông tin cá nhân (số điện thoại, Zalo, trường lớp) cho người lạ.",
        patterns=(
            r"\b(de lai|gui|cho|cho minh xin|xin)\s+(minh\s+)?(so dien thoai|sdt|so dt|zalo|facebook|fb|thong tin|dia chi|ten truong)\b",
            r"\b(dien|nhap)\s+(thong tin|ho ten|so dien thoai)\s+(vao|de)\b",
        ),
    ),
]

TRADE_RULES: List[Rule] = [
    _r(
        id="TRADE_ACCOUNT",
        signal=SIG_ADS,
        category=CATEGORY_ADS_SPAM,
        weight=0.3,
        reason="Rao mua bán/trao đổi tài khoản game — dễ mất nick và mất tiền, học sinh không nên tham gia.",
        patterns=(
            r"\b(mua|ban|nhuong|doi|sang)\s+(lai\s+)?(nick|acc|tai khoan|vat pham)\b",
            r"\b(nick|acc|tai khoan)\s+(gia re|gia mem|thanh ly)\b",
        ),
    ),
    _r(
        id="INVITE_FREE_OFFER",
        signal=SIG_INVITE,
        category=CATEGORY_SUSPICIOUS_INVITE,
        weight=0.3,
        reason="Người lạ hứa tặng quà/tài liệu/vé miễn phí nếu em đăng ký, tải app hoặc để lại thông tin.",
        patterns=(
            r"\b(duoc|dang ky)\s+(tang|moi|nhan)\s+\d*\s*(khoa hoc|ve|qua|tai lieu|vat pham|the qua tang|suat)?\b",
            r"\b(dang ky|tham gia|nhan tin|inbox|de lai|tai)\b.{0,30}?\b(de\s+)?(nhan|lay)\s+(qua|the|ve|tai lieu|khoa hoc|bang gia|phan qua)\b",
            r"\b(mien phi|free)\b.{0,30}?\b(dang ky|tai|link|nhom|inbox|nhan tin|de lai)\b",
            r"\b(tai|dung thu)\s+(ung dung|app|phan mem)\s+(moi|nay|hoc tap)\b",
            r"\b(tham gia|lam)\s+(khao sat|binh chon|bau chon)\b",
            r"\bnhom\s+(mua chung|ban hang|chia se hang)\b",
            r"\b(vao|tham gia)\b.{0,25}?\b(cho vui|cho re|cho biet)\b",
            r"\b(link|duong dan)\s+(nhom|group|trong bio|trong phan gioi thieu)\b",
        ),
    ),
    _r(
        id="INVITE_MINIGAME",
        signal=SIG_INVITE,
        category=CATEGORY_SUSPICIOUS_INVITE,
        weight=0.3,
        reason="Mời tham gia minigame/sự kiện của trang lạ để 'nhận quà'.",
        patterns=(
            r"\b(tham gia|choi|quay)\s+(minigame|mini game|su kien|event|vong quay|chuong trinh)\b",
            r"\b(admin|fanpage|trang)\s+.{0,20}\b(tang|nhan)\s+(qua|thuong)\b",
        ),
    ),
]

EWALLET_RULES: List[Rule] = [
    _r(
        id="MONEY_AMOUNT_REQUEST",
        signal=SIG_MONEY,
        category=CATEGORY_IMPERSONATION_RELATIVE,
        weight=0.35,
        reason="Yêu cầu nộp/chuyển một khoản tiền cụ thể qua tin nhắn.",
        patterns=(
            r"\b(dong|nop|chuyen|gui|nap|thanh toan|ung)\s+(ngay\s+|gap\s+|truoc\s+|het\s+|cho\s+)?(?<![\d.,])\d{1,3}(\.\d{3})*\s*(k|nghin|ngan|tram|trieu|tr|d|dong)\b",
        ),
    ),
    _r(
        id="MONEY_EWALLET",
        signal=SIG_MONEY,
        category=CATEGORY_IMPERSONATION_RELATIVE,
        weight=0.3,
        amplifier=True,
        reason="Chỉ định ví điện tử/số tài khoản lạ để nhận tiền — cách nhận tiền quen thuộc của kẻ lừa đảo.",
        patterns=(
            r"\b(momo|zalopay|viettel money|vnpay|shopee ?pay|vi dien tu)\b",
            r"\bqua\s+(momo|ngan hang|vi|chuyen khoan)\b",
        ),
    ),
]

SAFE_NOTICE_RULES: List[Rule] = [
    _r(
        id="SAFE_OTP_NOTIFICATION",
        signal=SIG_SAFE,
        category=CATEGORY_SAFE,
        weight=0.5,
        reason="Đây là tin nhắn ngân hàng *thông báo* mã OTP cho chính em, không phải ai đó đòi mã.",
        patterns=(
            r"\bma\s+(otp|xac thuc|giao dich|xac nhan)\b.{0,25}?\b(la|:)\s*\d{4,8}\b",
            r"\b(khong|tuyet doi khong)\s+(cung cap|chia se|tiet lo)\s+(ma\s+)?(otp|nay)\s+(cho|voi)\s+(bat ky|nguoi)\b",
            r"\b(hieu luc|het han)\s+(trong\s+)?\d+\s*(giay|phut)\b",
        ),
    ),
    _r(
        id="SAFE_CARRIER_NOTICE",
        signal=SIG_SAFE,
        category=CATEGORY_SAFE,
        weight=0.45,
        reason="Tin nhắn dịch vụ quen thuộc của nhà mạng (cú pháp tổng đài, gói cước, tài khoản thuê bao).",
        patterns=(
            r"\*\d{2,4}[\*\d]*#",
            r"\b(goi cuoc|thue bao|tra truoc|tra sau|tong dai|nhan tin|soan tin)\s+(cua|den|theo|gia han|dang ky)\b",
            r"\b(tk goc|tai khoan goc|data toc do cao|luu luong|dung luong)\b",
            r"\b(my viettel|my vnpt|my mobifone|app ngan hang|ung dung ngan hang)\b",
            r"\b(soan|bam goi|bam)\s+[a-z]{2,6}\s+(gui|den)\s+\d{3,4}\b",
            r"\b(quy khach|qk)\b.{0,40}?\b(goi cuoc|data|dung luong|hoa don|cuoc|diem thuong|tich diem|uu dai|tai khoan goc)\b",
            r"\b(chi tiet lien he|tong dai|hotline|cskh)\s*\d{3,4}\b",
        ),
    ),
]

ALL_RULES: List[Rule] = (
    IMPERSONATION_RULES
    + MONEY_RULES
    + OTP_RULES
    + THREAT_RULES
    + FREEBIE_RULES
    + PRIZE_RULES
    + PHISHING_LINK_RULES
    + JOB_RULES
    + GAMBLING_RULES
    + PRESSURE_RULES
    + LOW_RISK_RULES
    + EWALLET_RULES
    + DOWNLOAD_RULES
    + PII_RULES
    + TRADE_RULES
    + SAFE_RULES
    + SAFE_NOTICE_RULES
)

RULES_BY_ID: Dict[str, Rule] = {rule.id: rule for rule in ALL_RULES}

# Luat dung de trich xuat thuc the o Module 1 (`financial_keywords`, `urgency_markers`).
ENTITY_SIGNALS = {
    "financial_keywords": {SIG_MONEY, SIG_FREEBIE, SIG_PRIZE},
    "urgency_markers": {SIG_URGENCY},
}


def rules_for_signal(signal: str) -> List[Rule]:
    return [rule for rule in ALL_RULES if rule.signal == signal]
