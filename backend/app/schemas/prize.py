from typing import Optional
from pydantic import BaseModel, field_validator


class PrizeResponse(BaseModel):
    prize_name: str
    prize_description: str


class PrizeCreate(BaseModel):
    name: str
    description: str
    probability: float

    @field_validator("probability")
    @classmethod
    def validate_probability(cls, v: float) -> float:
        if not (0.0 < v <= 1.0):
            raise ValueError("Probability must be between 0 and 1")
        return round(v, 4)


class PrizeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    probability: Optional[float] = None
    is_active: Optional[bool] = None

    @field_validator("probability")
    @classmethod
    def validate_probability(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 < v <= 1.0):
            raise ValueError("Probability must be between 0 and 1")
        return round(v, 4) if v is not None else v


class PrizeAdminResponse(BaseModel):
    id: str
    name: str
    description: str
    probability: float
    is_active: bool
    total_assigned: int
