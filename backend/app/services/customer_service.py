import uuid
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.security import decode_access_token
from app.models.customer import Customer
from app.models.prize_assignment import PrizeAssignment
from app.services.prize_service import assign_prize
from app.services.notification import notify_customer, notify_shopkeeper

settings = get_settings()

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

        # ── Daily limit check ─────────────────────────────────────────────────
        if settings.daily_limit_hours > 0:
            since = datetime.now(tz=timezone.utc) - timedelta(hours=settings.daily_limit_hours)
            recent = await db.scalar(
                select(PrizeAssignment)
                .where(
                    PrizeAssignment.customer_id == existing.id,
                    PrizeAssignment.assigned_at >= since,
                )
                .limit(1)
            )
            if recent:
                logger.warning(f"Daily limit hit for +91{phone}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"You've already participated in the last {settings.daily_limit_hours} hours. Please visit us again later!",
                )

        customer = existing
    else:
        # ── Email uniqueness check ────────────────────────────────────────────
        if email:
            existing_email = await db.scalar(
                select(Customer).where(Customer.email == email)
            )
            if existing_email:
                logger.warning(f"Duplicate email registration attempt: {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email is already registered. Each email can only be used once.",
                )

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
