from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


# Import all models here so Alembic and relationship resolution can find them.
from app.models.user import User  # noqa: E402, F401
from app.models.target_config import TargetConfig  # noqa: E402, F401
from app.models.daily_log import DailyLog  # noqa: E402, F401
