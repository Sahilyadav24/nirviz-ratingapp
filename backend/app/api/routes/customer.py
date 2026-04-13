from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.customer import CustomerCreateRequest, CustomerCreateResponse
from app.services import customer_service

router = APIRouter()


@router.post("/register", response_model=CustomerCreateResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(
    payload: CustomerCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    customer, prize = await customer_service.register_customer(
        name=payload.name,
        phone=payload.phone,
        address=payload.address,
        session_token=payload.session_token,
        db=db,
        email=payload.email,
    )
    return CustomerCreateResponse(
        customer_id=str(customer.id),
        name=customer.name,
        message="Registration successful",
    )
