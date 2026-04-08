from app.core.config import get_settings
from app.core.logger import get_logger
from app.services.sms import send_sms
from app.services.email_service import send_shopkeeper_email

settings = get_settings()
logger = get_logger("notification")


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
        logger.info(f"Customer SMS notification sent to +91{phone}")
    except Exception as e:
        logger.error(f"Failed to send customer SMS to +91{phone}: {e}")


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
        logger.info(f"Shopkeeper SMS notification sent to +91{shopkeeper}")
    except Exception as e:
        logger.error(f"Failed to send shopkeeper SMS to +91{shopkeeper}: {e}")

    try:
        send_shopkeeper_email(name, phone, address, prize_name)
    except Exception as e:
        logger.error(f"Failed to send shopkeeper email: {e}")
