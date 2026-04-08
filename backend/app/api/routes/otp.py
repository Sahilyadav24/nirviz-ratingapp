from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.otp import OtpSendRequest, OtpVerifyRequest, OtpVerifyResponse
from app.services import otp_service

router = APIRouter()


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_otp(payload: OtpSendRequest, db: AsyncSession = Depends(get_db)):
    await otp_service.send_otp(payload.phone, payload.email, db)
    return {"message": "OTP sent to your email", "phone": payload.phone}


@router.post("/verify", response_model=OtpVerifyResponse)
async def verify_otp(payload: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    token = await otp_service.verify_otp(payload.phone, payload.otp, db)
    return OtpVerifyResponse(verified=True, session_token=token)
