from pydantic import BaseModel


class PrizeResponse(BaseModel):
    prize_name: str
    prize_description: str


class PrizeCreate(BaseModel):
    name: str
    description: str
    probability: float          # 0.0 to 1.0 — must sum to 1.0 across all active prizes

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Free Dessert",
                "description": "A complimentary dessert on your next visit!",
                "probability": 0.3,
            }
        }
