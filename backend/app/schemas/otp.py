from pydantic import BaseModel, EmailStr, field_validator
import re


class OtpSendRequest(BaseModel):
    phone: str
    email: EmailStr

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        if not re.fullmatch(r"[6-9]\d{9}", cleaned):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return cleaned


class OtpVerifyRequest(BaseModel):
    phone: str
    otp: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        if not re.fullmatch(r"[6-9]\d{9}", cleaned):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return cleaned

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("OTP must be exactly 6 digits")
        return v


class OtpVerifyResponse(BaseModel):
    verified: bool
    session_token: str
