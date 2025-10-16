import os
from email.message import EmailMessage
from pathlib import Path

from aiosmtplib import SMTP, SMTPResponseException

from jinja2 import Environment, FileSystemLoader


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

app_dir = Path(__file__).parent.parent

env = Environment(loader=FileSystemLoader(str(app_dir)))
template = env.get_template("./templates/mailing/email-verify/verification-request.html")


async def send_otp_email(to_email: str, otp_code: str):
    html_content = template.render(code=otp_code, email=to_email)

    message = EmailMessage()
    message["From"] = os.getenv("SMTP_USER")
    message["To"] = to_email
    message["Subject"] = "Ваш код подтверждения почты"
    message.set_content(f"Ваш код подтверждения почты: {otp_code}")

    message.add_alternative(html_content, subtype="html")

    smtp = SMTP(
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True
    )

    try:
        await smtp.connect()
        await smtp.login(SMTP_USER, SMTP_PASS)
        await smtp.send_message(message)
        await smtp.quit()
    except SMTPResponseException as e:
        print(f"Error sending email: {e}")
