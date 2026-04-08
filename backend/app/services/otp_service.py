from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.security import generate_otp, hash_otp, verify_otp, otp_expiry, create_access_token
from app.models.otp_log import OtpLog
from app.services.email_service import send_otp_email

settings = get_settings()
logger = get_logger("otp")


async def send_otp(phone: str, email: str, db: AsyncSession) -> None:
    """Generate OTP, save hashed to DB, send via email."""

    # ── Rate limit ────────────────────────────────────────────────────────────
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
        logger.warning(f"Rate limit hit for phone +91{phone} ({recent_count} attempts in {settings.otp_cooldown_minutes} min)")
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
    await db.flush()

    # ── Send via Email ────────────────────────────────────────────────────────
    try:
        send_otp_email(email, otp)
        logger.info(f"OTP sent to {email} for phone +91{phone}")
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email} for phone +91{phone}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send OTP. Please try again.",
        ) from e


async def verify_otp(phone: str, otp: str, db: AsyncSession) -> str:
    """Verify OTP. Returns a JWT session token on success."""

    result = await db.execute(
        select(OtpLog)
        .where(OtpLog.phone == phone, OtpLog.used == False)
        .order_by(OtpLog.created_at.desc())
        .limit(1)
    )
    log = result.scalar_one_or_none()

    if not log:
        logger.warning(f"OTP verify failed for +91{phone}: no active OTP found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this number. Please request a new one.",
        )

    if log.attempts >= settings.otp_max_attempts:
        logger.warning(f"OTP verify failed for +91{phone}: max attempts exceeded")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum attempts exceeded. Please request a new OTP.",
        )

    log.attempts += 1
    await db.flush()

    from app.core.security import verify_otp as check_otp
    if not check_otp(otp, log.otp_hash, log.expires_at):
        logger.warning(f"OTP verify failed for +91{phone}: invalid or expired OTP (attempt {log.attempts})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP.",
        )

    log.used = True
    logger.info(f"OTP verified successfully for +91{phone}")

    token = create_access_token(subject=phone, expires_delta=timedelta(minutes=10))
    return token
