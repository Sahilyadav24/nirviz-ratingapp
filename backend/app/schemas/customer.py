from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class CustomerCreateRequest(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    address: str
    session_token: str          # issued by /otp/verify — proves OTP was passed

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be at most 100 characters")
        if not re.fullmatch(r"[A-Za-z\s]+", v):
            raise ValueError("Name can only contain letters and spaces")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        if not re.fullmatch(r"[6-9]\d{9}", cleaned):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return cleaned

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Address must be at least 5 characters")
        if len(v) > 500:
            raise ValueError("Address must be at most 500 characters")
        return v


class CustomerCreateResponse(BaseModel):
    customer_id: str
    name: str
    message: str
