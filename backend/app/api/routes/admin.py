import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logger import get_logger

logger = get_logger("admin")
from app.models.customer import Customer
from app.models.prize import Prize
from app.models.prize_assignment import PrizeAssignment
from app.schemas.prize import PrizeCreate, PrizeUpdate, PrizeAdminResponse

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
    email: Optional[str]
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
            email=customer.email,
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


# ── Prize CRUD ────────────────────────────────────────────────────────────────

def _check_admin(password: Optional[str]) -> None:
    if password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password.")


@router.get("/prizes", response_model=list[PrizeAdminResponse])
async def list_prizes(
    x_admin_password: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)
    result = await db.execute(select(Prize).order_by(Prize.created_at.asc()))
    prizes = result.scalars().all()

    counts_result = await db.execute(
        select(PrizeAssignment.prize_id, func.count(PrizeAssignment.id))
        .group_by(PrizeAssignment.prize_id)
    )
    counts = {str(row[0]): row[1] for row in counts_result.all()}

    return [
        PrizeAdminResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            probability=p.probability,
            is_active=p.is_active,
            total_assigned=counts.get(str(p.id), 0),
        )
        for p in prizes
    ]


@router.post("/prizes", response_model=PrizeAdminResponse, status_code=201)
async def create_prize(
    payload: PrizeCreate,
    x_admin_password: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)
    prize = Prize(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        probability=payload.probability,
        is_active=True,
    )
    db.add(prize)
    await db.flush()
    logger.info(f"Prize created: {prize.name}")
    return PrizeAdminResponse(
        id=str(prize.id),
        name=prize.name,
        description=prize.description,
        probability=prize.probability,
        is_active=prize.is_active,
        total_assigned=0,
    )


@router.put("/prizes/{prize_id}", response_model=PrizeAdminResponse)
async def update_prize(
    prize_id: str,
    payload: PrizeUpdate,
    x_admin_password: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)
    prize = await db.scalar(select(Prize).where(Prize.id == uuid.UUID(prize_id)))
    if not prize:
        raise HTTPException(status_code=404, detail="Prize not found.")

    if payload.name is not None:
        prize.name = payload.name
    if payload.description is not None:
        prize.description = payload.description
    if payload.probability is not None:
        prize.probability = payload.probability
    if payload.is_active is not None:
        prize.is_active = payload.is_active

    await db.flush()
    logger.info(f"Prize updated: {prize.name}")

    count = await db.scalar(
        select(func.count(PrizeAssignment.id)).where(PrizeAssignment.prize_id == prize.id)
    )
    return PrizeAdminResponse(
        id=str(prize.id),
        name=prize.name,
        description=prize.description,
        probability=prize.probability,
        is_active=prize.is_active,
        total_assigned=count or 0,
    )


@router.patch("/prizes/{prize_id}/toggle", response_model=PrizeAdminResponse)
async def toggle_prize(
    prize_id: str,
    x_admin_password: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)
    prize = await db.scalar(select(Prize).where(Prize.id == uuid.UUID(prize_id)))
    if not prize:
        raise HTTPException(status_code=404, detail="Prize not found.")

    prize.is_active = not prize.is_active
    await db.flush()
    logger.info(f"Prize {'activated' if prize.is_active else 'deactivated'}: {prize.name}")

    count = await db.scalar(
        select(func.count(PrizeAssignment.id)).where(PrizeAssignment.prize_id == prize.id)
    )
    return PrizeAdminResponse(
        id=str(prize.id),
        name=prize.name,
        description=prize.description,
        probability=prize.probability,
        is_active=prize.is_active,
        total_assigned=count or 0,
    )


@router.delete("/prizes/{prize_id}", status_code=204)
async def delete_prize(
    prize_id: str,
    x_admin_password: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)
    prize = await db.scalar(select(Prize).where(Prize.id == uuid.UUID(prize_id)))
    if not prize:
        raise HTTPException(status_code=404, detail="Prize not found.")

    try:
        await db.delete(prize)
        await db.flush()
        logger.info(f"Prize deleted: {prize.name}")
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete prize — it has been assigned to customers. Deactivate it instead.",
        )


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics")
async def get_analytics(
    x_admin_password: Optional[str] = Header(None),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD (IST)"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD (IST)"),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)

    # Build optional date range filter (applied to IST dates)
    date_filter_customers = ""
    date_filter_assignments = ""
    if start_date:
        date_filter_customers += f" AND DATE(created_at AT TIME ZONE 'Asia/Kolkata') >= '{start_date}'"
        date_filter_assignments += f" AND DATE(assigned_at AT TIME ZONE 'Asia/Kolkata') >= '{start_date}'"
    if end_date:
        date_filter_customers += f" AND DATE(created_at AT TIME ZONE 'Asia/Kolkata') <= '{end_date}'"
        date_filter_assignments += f" AND DATE(assigned_at AT TIME ZONE 'Asia/Kolkata') <= '{end_date}'"

    # Prize distribution (filtered by assignment date)
    # Build JOIN condition with table alias for date filters
    pa_date_filter = ""
    if start_date:
        pa_date_filter += f" AND DATE(pa.assigned_at AT TIME ZONE 'Asia/Kolkata') >= '{start_date}'"
    if end_date:
        pa_date_filter += f" AND DATE(pa.assigned_at AT TIME ZONE 'Asia/Kolkata') <= '{end_date}'"

    prize_dist_rows = await db.execute(text(f"""
        SELECT p.name, COUNT(pa.id) AS count
        FROM prizes p
        LEFT JOIN prize_assignments pa ON pa.prize_id = p.id {pa_date_filter}
        GROUP BY p.name
        ORDER BY count DESC
    """))

    # Daily registrations — last 30 days or filtered range (IST)
    if start_date or end_date:
        daily_where = f"WHERE 1=1 {date_filter_customers}"
    else:
        daily_where = "WHERE created_at >= NOW() - INTERVAL '30 days'"

    daily_rows = await db.execute(text(f"""
        SELECT DATE(created_at AT TIME ZONE 'Asia/Kolkata') AS day, COUNT(*) AS count
        FROM customers
        {daily_where}
        GROUP BY day
        ORDER BY day
    """))

    # Total customers (filtered)
    total_customers_row = await db.execute(text(f"""
        SELECT COUNT(*) FROM customers WHERE 1=1 {date_filter_customers}
    """))
    total_customers = total_customers_row.scalar() or 0

    # Repeat visitors (filtered)
    repeat_result = await db.execute(text(f"""
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM prize_assignments
            WHERE 1=1 {date_filter_assignments}
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        ) sub
    """))
    repeat_count = repeat_result.scalar() or 0

    # Peak hours in IST (filtered)
    peak_rows = await db.execute(text(f"""
        SELECT EXTRACT(HOUR FROM assigned_at AT TIME ZONE 'Asia/Kolkata')::int AS hour,
               COUNT(*) AS count
        FROM prize_assignments
        WHERE 1=1 {date_filter_assignments}
        GROUP BY hour
        ORDER BY hour
    """))

    # Total assignments (filtered)
    total_assignments_row = await db.execute(text(f"""
        SELECT COUNT(*) FROM prize_assignments WHERE 1=1 {date_filter_assignments}
    """))
    total_assignments = total_assignments_row.scalar() or 0

    repeat_pct = round((repeat_count / total_customers * 100) if total_customers > 0 else 0, 1)

    return {
        "prize_distribution": [
            {"name": r[0], "count": int(r[1])} for r in prize_dist_rows.all()
        ],
        "daily_registrations": [
            {"date": str(r[0]), "count": int(r[1])} for r in daily_rows.all()
        ],
        "repeat_visitor_percentage": repeat_pct,
        "peak_hours": [
            {"hour": int(r[0]), "count": int(r[1])} for r in peak_rows.all()
        ],
        "total_assignments": int(total_assignments),
    }
