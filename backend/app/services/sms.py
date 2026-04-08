import httpx
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

MSG91_OTP_URL = "https://api.msg91.com/api/v5/otp"
MSG91_SMS_URL = "https://api.msg91.com/api/v5/flow/"


def _is_mock() -> bool:
    """Use mock mode if MSG91 credentials are not configured."""
    return not settings.msg91_authkey or settings.app_env == "development" and not settings.msg91_authkey


def send_otp_sms(phone: str, otp: str) -> None:
    """Send OTP via SMS. Uses mock (console log) in dev if MSG91 not configured."""
    if _is_mock():
        logger.warning("=" * 50)
        logger.warning(f"[MOCK SMS] OTP for {phone}: {otp}")
        logger.warning("=" * 50)
        print(f"\n{'='*50}\n[MOCK SMS] OTP for +91{phone} is: {otp}\n{'='*50}\n")
        return

    response = httpx.post(
        MSG91_OTP_URL,
        params={
            "template_id": settings.msg91_otp_template_id,
            "mobile": f"91{phone}",
            "authkey": settings.msg91_authkey,
            "otp": otp,
        },
        timeout=10,
    )
    response.raise_for_status()


def send_sms(phone: str, message: str) -> None:
    """Send a plain SMS. Uses mock (console log) in dev if MSG91 not configured."""
    if _is_mock():
        logger.warning(f"[MOCK SMS] To +91{phone}: {message}")
        print(f"\n[MOCK SMS] To +91{phone}:\n{message}\n")
        return

    payload = {
        "flow_id": settings.msg91_otp_template_id,
        "sender": settings.msg91_sender_id,
        "mobiles": f"91{phone}",
        "body": message,
    }
    headers = {
        "authkey": settings.msg91_authkey,
        "Content-Type": "application/json",
    }
    response = httpx.post(MSG91_SMS_URL, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
