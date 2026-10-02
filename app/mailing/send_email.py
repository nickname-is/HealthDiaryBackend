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
template_verification = env.get_template(
    "./templates/mailing/email-verify/verification-request.html"
)
template_reset_password_otp = env.get_template(
    "./templates/mailing/reset-password/reset-password-otp.html"
)


async def send_email(message: EmailMessage) -> None:
    smtp = SMTP(hostname=SMTP_HOST, port=SMTP_PORT, start_tls=True)

    try:
        await smtp.connect()
        await smtp.login(SMTP_USER, SMTP_PASS)
        await smtp.send_message(message)
        await smtp.quit()
    except SMTPResponseException as e:
        print(f"Error sending email: {e}")


async def send_otp_email(to_email: str, otp_code: str, first_name: str) -> None:
    html_content = template_verification.render(code=otp_code, first_name=first_name)

    message = EmailMessage()
    message["From"] = os.getenv("SMTP_USER")
    message["To"] = to_email
    message["Subject"] = "Ваш код подтверждения почты"
    message.set_content(f"Ваш код подтверждения почты: {otp_code}")

    message.add_alternative(html_content, subtype="html")

    await send_email(message)


async def send_otp_reset_password(
    to_email: str, otp_code: str, first_name: str
) -> None:
    html_content = template_reset_password_otp.render(
        code=otp_code, first_name=first_name
    )

    message = EmailMessage()
    message["From"] = os.getenv("SMTP_USER")
    message["To"] = to_email
    message["Subject"] = "Ваш код подтверждения для сброса пароля"
    message.set_content(f"Ваш код подтверждения для сброса пароля: {otp_code}")

    message.add_alternative(html_content, subtype="html")

    await send_email(message)
