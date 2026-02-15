import uuid
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    firebase_uid: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default="now()",
    )

    # Relationships
    target_config = relationship(
        "TargetConfig",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    daily_logs = relationship(
        "DailyLog",
        back_populates="user",
        lazy="selectin",
    )
