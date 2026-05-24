import os
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
load_dotenv('/app/.env')


def run_email(content: str, attachments: list[str] | None = None) -> bool:
    """결과 본문 + 선택적 첨부파일을 네이버 SMTP로 발송."""
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        print("❌ 이메일 설정이 없습니다.")
        return False

    msg = MIMEMultipart()
    msg["Subject"] = "🚀 ARIA — Auto Vibe Coding Engine 결과"
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(content, "plain", "utf-8"))

    for path in attachments or []:
        if not path or not os.path.isfile(path):
            print(f"⚠️ 첨부파일 없음: {path}")
            continue
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(path)}"',
        )
        msg.attach(part)
        print(f"📎 첨부 추가: {os.path.basename(path)}")

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"✅ 이메일 발송 완료 → {recipient}")
        return True
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
        return False
