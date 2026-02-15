import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Actual values (nullable for partial logging)
    calories_actual: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    protein_actual: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    sleep_actual: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )

    # Binary habit indicators
    workout_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )
    is_period_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # Target snapshot (frozen at creation, NOT nullable)
    calorie_target_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    protein_target_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    sleep_target_snapshot: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default="now()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default="now()",
        onupdate=datetime.utcnow,
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_logs_user_date"),
        CheckConstraint("calories_actual >= 0", name="ck_log_calories_non_negative"),
        CheckConstraint("protein_actual >= 0", name="ck_log_protein_non_negative"),
        CheckConstraint("sleep_actual >= 0", name="ck_log_sleep_non_negative"),
        CheckConstraint(
            "calorie_target_snapshot >= 0",
            name="ck_log_cal_snapshot_non_negative",
        ),
        CheckConstraint(
            "protein_target_snapshot >= 0",
            name="ck_log_prot_snapshot_non_negative",
        ),
        CheckConstraint(
            "sleep_target_snapshot >= 0",
            name="ck_log_sleep_snapshot_non_negative",
        ),
    )

    # Relationships
    user = relationship("User", back_populates="daily_logs")
