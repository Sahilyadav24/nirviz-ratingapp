import uuid

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.security import decode_access_token
from app.models.customer import Customer
from app.services.prize_service import assign_prize
from app.services.notification import notify_customer, notify_shopkeeper

logger = get_logger("customer")


async def register_customer(
    name: str,
    phone: str,
    address: str,
    session_token: str,
    db: AsyncSession,
    email: str | None = None,
) -> tuple[Customer, object]:
    """
    Validate session token, save customer, assign prize, send notifications.
    Returns (customer, prize).
    """

    # ── Validate session token ────────────────────────────────────────────────
    try:
        payload = decode_access_token(session_token)
        token_phone = payload.get("sub")
    except JWTError:
        logger.warning(f"Invalid session token used for phone +91{phone}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please verify OTP again.",
        )

    if token_phone != phone:
        logger.warning(f"Session phone mismatch: token={token_phone}, submitted={phone}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session phone does not match submitted phone.",
        )

    # ── Check if returning customer ───────────────────────────────────────────
    existing = await db.scalar(
        select(Customer).where(Customer.phone == phone)
    )

    if existing:
        logger.info(f"Returning customer: {existing.name} (+91{phone})")
        customer = existing
    else:
        customer = Customer(
            id=uuid.uuid4(),
            name=name,
            phone=phone,
            email=email,
            address=address,
        )
        db.add(customer)
        try:
            await db.flush()
            logger.info(f"New customer registered: {name} (+91{phone})")
        except IntegrityError:
            logger.error(f"IntegrityError on registration for +91{phone}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration failed. Please try again.",
            )

    # ── Assign prize ──────────────────────────────────────────────────────────
    prize = await assign_prize(customer.id, db)
    logger.info(f"{customer.name} (+91{phone}) won: {prize.name}")

    # ── Send notifications ────────────────────────────────────────────────────
    notify_customer(customer.name, phone, prize.name, prize.description)
    notify_shopkeeper(customer.name, phone, customer.address, prize.name)

    return customer, prize
