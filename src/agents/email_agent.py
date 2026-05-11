import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv('/app/.env')

def run_email(content: str) -> bool:
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        print("❌ 이메일 설정이 없습니다.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚀 Auto Vibe Coding Engine 결과"
    msg["From"] = sender
    msg["To"] = recipient

    text_part = MIMEText(content, "plain", "utf-8")
    msg.attach(text_part)

    try:
        with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"✅ 이메일 발송 완료 → {recipient}")
        return True
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
        return False
