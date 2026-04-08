from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logger import get_logger

logger = get_logger("admin")
from app.models.customer import Customer
from app.models.prize import Prize
from app.models.prize_assignment import PrizeAssignment

settings = get_settings()
router = APIRouter()

IST = timezone(timedelta(hours=5, minutes=30))


def to_ist(dt: Optional[datetime]) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p")


class VisitRecord(BaseModel):
    prize_name: str
    visited_at: str


class CustomerRecord(BaseModel):
    name: str
    phone: str
    address: str
    visit_count: int
    visits: list[VisitRecord]
    first_visit: str
    last_visit: str


class AdminDashboard(BaseModel):
    total_customers: int
    today_registrations: int
    customers: list[CustomerRecord]


@router.get("/customers", response_model=AdminDashboard)
async def get_all_customers(
    x_admin_password: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if x_admin_password != settings.admin_password:
        logger.warning("Admin dashboard: invalid password attempt")
        raise HTTPException(status_code=401, detail="Invalid admin password.")

    logger.info("Admin dashboard accessed")

    result = await db.execute(
        select(Customer).order_by(Customer.created_at.desc())
    )
    customers = result.scalars().all()

    today_ist = datetime.now(IST).date()
    today_count = sum(
        1 for c in customers
        if (c.created_at.replace(tzinfo=timezone.utc) if c.created_at.tzinfo is None else c.created_at)
        .astimezone(IST).date() == today_ist
    )

    records = []
    for customer in customers:
        pa_result = await db.execute(
            select(PrizeAssignment, Prize)
            .join(Prize, Prize.id == PrizeAssignment.prize_id)
            .where(PrizeAssignment.customer_id == customer.id)
            .order_by(PrizeAssignment.assigned_at.asc())
        )
        assignments = pa_result.all()

        visits = [
            VisitRecord(prize_name=prize.name, visited_at=to_ist(pa.assigned_at))
            for pa, prize in assignments
        ]

        first_visit = to_ist(assignments[0][0].assigned_at) if assignments else to_ist(customer.created_at)
        last_visit = to_ist(assignments[-1][0].assigned_at) if assignments else to_ist(customer.created_at)

        records.append(CustomerRecord(
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            visit_count=len(visits) if visits else 1,
            visits=visits,
            first_visit=first_visit,
            last_visit=last_visit,
        ))

    return AdminDashboard(
        total_customers=len(customers),
        today_registrations=today_count,
        customers=records,
    )
