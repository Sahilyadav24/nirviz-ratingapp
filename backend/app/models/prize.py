import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prize(Base):
    __tablename__ = "prizes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Probability weight (0.0–1.0). All active prizes must sum to 1.0.
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assignments: Mapped[list["PrizeAssignment"]] = relationship(
        "PrizeAssignment", back_populates="prize"
    )

    def __repr__(self) -> str:
        return f"<Prize id={self.id} name={self.name} prob={self.probability}>"
