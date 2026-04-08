from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_otp, hash_otp, verify_otp, otp_expiry, create_access_token
from app.models.otp_log import OtpLog
from app.services.email_service import send_otp_email

settings = get_settings()


async def send_otp(phone: str, email: str, db: AsyncSession) -> None:
    """Generate OTP, save hashed to DB, send via email."""

    # ── Rate limit: max 3 OTP requests per phone per cooldown window ──────────
    window_start = datetime.now(tz=timezone.utc) - timedelta(
        minutes=settings.otp_cooldown_minutes
    )
    recent_count = await db.scalar(
        select(func.count(OtpLog.id)).where(
            OtpLog.phone == phone,
            OtpLog.created_at >= window_start,
        )
    )
    if recent_count >= settings.otp_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many OTP requests. Try again after {settings.otp_cooldown_minutes} minutes.",
        )

    # ── Generate and store ────────────────────────────────────────────────────
    otp = generate_otp()
    log = OtpLog(
        phone=phone,
        otp_hash=hash_otp(otp),
        expires_at=otp_expiry(),
    )
    db.add(log)
    await db.flush()  # get ID without committing yet

    # ── Send via Email ────────────────────────────────────────────────────────
    try:
        send_otp_email(email, otp)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send OTP. Please try again.",
        ) from e


async def verify_otp(phone: str, otp: str, db: AsyncSession) -> str:
    """Verify OTP. Returns a JWT session token on success."""

    # ── Find latest unused OTP for this phone ─────────────────────────────────
    result = await db.execute(
        select(OtpLog)
        .where(OtpLog.phone == phone, OtpLog.used == False)
        .order_by(OtpLog.created_at.desc())
        .limit(1)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this number. Please request a new one.",
        )

    # ── Check max attempts ────────────────────────────────────────────────────
    if log.attempts >= settings.otp_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum attempts exceeded. Please request a new OTP.",
        )

    # ── Increment attempt count ───────────────────────────────────────────────
    log.attempts += 1
    await db.flush()

    # ── Verify hash + expiry ──────────────────────────────────────────────────
    from app.core.security import verify_otp as check_otp
    if not check_otp(otp, log.otp_hash, log.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP.",
        )

    # ── Mark as used ──────────────────────────────────────────────────────────
    log.used = True

    # ── Issue session token (valid 10 min — just enough to submit the form) ───
    token = create_access_token(subject=phone, expires_delta=timedelta(minutes=10))
    return token
