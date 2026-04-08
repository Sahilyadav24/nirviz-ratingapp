import httpx

from app.core.config import get_settings

settings = get_settings()

META_API_URL = (
    "https://graph.facebook.com/{version}/{phone_number_id}/messages"
)


def _url() -> str:
    return META_API_URL.format(
        version=settings.whatsapp_api_version,
        phone_number_id=settings.whatsapp_phone_number_id,
    )


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }


def send_whatsapp_message(to_phone: str, body: str) -> None:
    """
    Send a WhatsApp text message via Meta Cloud API.
    to_phone: 10-digit Indian number without country code (e.g. '9876543210')
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": f"91{to_phone}",
        "type": "text",
        "text": {"body": body},
    }
    response = httpx.post(_url(), headers=_headers(), json=payload, timeout=10)
    response.raise_for_status()


def send_otp_message(to_phone: str, otp: str) -> None:
    body = (
        f"Your NIRVIZ Resort OTP is: *{otp}*\n"
        f"Valid for {settings.otp_expiry_minutes} minutes.\n"
        f"Do not share this with anyone."
    )
    send_whatsapp_message(to_phone, body)
