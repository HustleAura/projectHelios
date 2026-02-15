import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class TargetConfig(Base):
    __tablename__ = "target_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    calorie_target: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    protein_target: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    sleep_target: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default="now()",
        onupdate=datetime.utcnow,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("calorie_target >= 0", name="ck_target_calories_non_negative"),
        CheckConstraint("protein_target >= 0", name="ck_target_protein_non_negative"),
        CheckConstraint("sleep_target >= 0", name="ck_target_sleep_non_negative"),
    )

    # Relationships
    user = relationship("User", back_populates="target_config")
