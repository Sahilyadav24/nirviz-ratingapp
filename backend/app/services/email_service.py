import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings

settings = get_settings()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_shopkeeper_email(customer_name: str, customer_phone: str, customer_address: str, prize_name: str) -> None:
    """Notify shopkeeper via email when a customer wins a prize."""
    if not settings.shopkeeper_email:
        return

    msg = MIMEMultipart()
    msg["From"] = settings.gmail_sender
    msg["To"] = settings.shopkeeper_email
    msg["Subject"] = f"New Registration — {customer_name} won {prize_name}"

    body = f"""
New customer registration at NIRVIZ Resort Fast Food & Cafe.

Customer Details:
  Name    : {customer_name}
  Phone   : +91{customer_phone}
  Address : {customer_address}

Prize Won : {prize_name}

— NIRVIZ Resort System
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(settings.gmail_sender, settings.gmail_app_password)
        server.sendmail(settings.gmail_sender, settings.shopkeeper_email, msg.as_string())


def send_otp_email(to_email: str, otp: str) -> None:
    """Send OTP via Gmail SMTP."""
    msg = MIMEMultipart()
    msg["From"] = settings.gmail_sender
    msg["To"] = to_email
    msg["Subject"] = "Your NIRVIZ Resort OTP"

    body = f"""
Hello,

Your OTP for NIRVIZ Resort registration is:

    {otp}

This OTP is valid for {settings.otp_expiry_minutes} minutes.
Do not share this with anyone.

— NIRVIZ Resort Fast Food & Cafe
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(settings.gmail_sender, settings.gmail_app_password)
        server.sendmail(settings.gmail_sender, to_email, msg.as_string())
