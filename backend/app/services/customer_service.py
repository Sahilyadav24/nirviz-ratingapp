import uuid

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.customer import Customer
from app.services.prize_service import assign_prize
from app.services.notification import notify_customer, notify_shopkeeper


async def register_customer(
    name: str,
    phone: str,
    address: str,
    session_token: str,
    db: AsyncSession,
) -> tuple[Customer, object]:
    """
    Validate session token, save customer, assign prize, send notifications.
    Returns (customer, prize).
    """

    # ── Validate session token issued by /otp/verify ──────────────────────────
    try:
        payload = decode_access_token(session_token)
        token_phone = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please verify OTP again.",
        )

    if token_phone != phone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session phone does not match submitted phone.",
        )

    # ── Check if phone already registered (returning customer) ───────────────
    existing = await db.scalar(
        select(Customer).where(Customer.phone == phone)
    )

    if existing:
        # Returning customer — just assign a new prize, don't create new record
        customer = existing
    else:
        # New customer — save to DB
        customer = Customer(
            id=uuid.uuid4(),
            name=name,
            phone=phone,
            address=address,
        )
        db.add(customer)
        try:
            await db.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration failed. Please try again.",
            )

    # ── Assign prize ──────────────────────────────────────────────────────────
    prize = await assign_prize(customer.id, db)

    # ── Send notifications (non-blocking — failures are swallowed) ────────────
    notify_customer(name, phone, prize.name, prize.description)
    notify_shopkeeper(name, phone, address, prize.name)

    return customer, prize
