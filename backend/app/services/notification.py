from app.core.config import get_settings
from app.services.sms import send_sms
from app.services.email_service import send_shopkeeper_email

settings = get_settings()


def notify_customer(name: str, phone: str, prize_name: str, prize_description: str) -> None:
    message = (
        f"Congratulations {name}! "
        f"Thank you for visiting NIRVIZ Resort Fast Food & Cafe. "
        f"You have won: {prize_name}. "
        f"{prize_description}. "
        f"Show this SMS to our staff to claim your prize."
    )
    try:
        send_sms(phone, message)
    except Exception:
        pass  # notification failure should not block the response


def notify_shopkeeper(name: str, phone: str, address: str, prize_name: str) -> None:
    shopkeeper = settings.shopkeeper_phone.lstrip("+")
    if shopkeeper.startswith("91") and len(shopkeeper) == 12:
        shopkeeper = shopkeeper[2:]

    message = (
        f"New Registration - "
        f"Name: {name}, "
        f"Phone: +91{phone}, "
        f"Address: {address}, "
        f"Prize Won: {prize_name}"
    )
    try:
        send_sms(shopkeeper, message)
    except Exception:
        pass  # notification failure should not block the response

    try:
        send_shopkeeper_email(name, phone, address, prize_name)
    except Exception:
        pass  # email failure should not block the response
