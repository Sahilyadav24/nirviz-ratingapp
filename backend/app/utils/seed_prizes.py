"""
Run once to insert default prizes into the DB.
Usage:  docker compose run --rm backend python -m app.utils.seed_prizes
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.prize import Prize

PRIZES = [
    {"name": "Free Welcome Drink",       "description": "1 complimentary welcome drink on your next visit.",      "probability": 0.40},
    {"name": "10% Discount Coupon",      "description": "10% off on your next total bill at NIRVIZ.",             "probability": 0.30},
    {"name": "Free Dessert",             "description": "1 complimentary dessert of your choice.",                "probability": 0.20},
    {"name": "Lucky Draw Entry",         "description": "You're entered into our monthly lucky draw! Stay tuned.","probability": 0.09},
    {"name": "50% Off on Next Visit",    "description": "50% discount on your entire next bill at NIRVIZ!",       "probability": 0.01},
]


async def seed():
    async with AsyncSessionLocal() as db:
        for p in PRIZES:
            prize = Prize(name=p["name"], description=p["description"], probability=p["probability"])
            db.add(prize)
        await db.commit()
        print(f"✅ Seeded {len(PRIZES)} prizes successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
