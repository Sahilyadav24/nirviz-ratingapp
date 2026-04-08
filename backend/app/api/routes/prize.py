from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.prize import PrizeResponse
from app.services import prize_service

router = APIRouter()


@router.get("/{customer_id}", response_model=PrizeResponse)
async def get_prize(customer_id: str, db: AsyncSession = Depends(get_db)):
    prize = await prize_service.get_customer_prize(customer_id, db)
    return PrizeResponse(
        prize_name=prize.name,
        prize_description=prize.description,
    )
