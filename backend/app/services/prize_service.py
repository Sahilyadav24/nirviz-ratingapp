import random

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prize import Prize
from app.models.prize_assignment import PrizeAssignment


async def assign_prize(customer_id, db: AsyncSession) -> Prize:
    """Weighted random prize selection. Saves assignment to DB."""

    # ── Fetch all active prizes ───────────────────────────────────────────────
    result = await db.execute(
        select(Prize).where(Prize.is_active == True)
    )
    prizes = result.scalars().all()

    if not prizes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No active prizes available. Please contact staff.",
        )

    # ── Weighted random selection ─────────────────────────────────────────────
    weights = [p.probability for p in prizes]
    selected_prize = random.choices(prizes, weights=weights, k=1)[0]

    # ── Save assignment ───────────────────────────────────────────────────────
    assignment = PrizeAssignment(
        customer_id=customer_id,
        prize_id=selected_prize.id,
    )
    db.add(assignment)
    await db.flush()

    return selected_prize


async def get_customer_prize(customer_id: str, db: AsyncSession) -> Prize:
    """Fetch the most recently assigned prize for a customer."""
    result = await db.execute(
        select(Prize)
        .join(PrizeAssignment, PrizeAssignment.prize_id == Prize.id)
        .where(PrizeAssignment.customer_id == customer_id)
        .order_by(PrizeAssignment.assigned_at.desc())
        .limit(1)
    )
    prize = result.scalar_one_or_none()

    if not prize:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prize not found for this customer.",
        )
    return prize
