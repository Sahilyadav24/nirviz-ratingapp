import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"


# ─── OTP ──────────────────────────────────────────────────────────────────────

def generate_otp() -> str:
    """Cryptographically secure 6-digit OTP."""
    return str(secrets.randbelow(900_000) + 100_000)


def hash_otp(otp: str) -> str:
    """SHA-256 hash — never store plain OTPs."""
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp(plain_otp: str, hashed_otp: str, expires_at: datetime) -> bool:
    now = datetime.now(tz=timezone.utc)
    # normalise stored datetime to UTC-aware for comparison
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        return False
    return hashlib.sha256(plain_otp.encode()).hexdigest() == hashed_otp


def otp_expiry() -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.otp_expiry_minutes
    )


# ─── JWT (admin auth) ─────────────────────────────────────────────────────────

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(hours=8)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
