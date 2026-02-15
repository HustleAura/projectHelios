import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.target_config import TargetConfig
from app.repositories.daily_log_repo import DailyLogRepository
from app.repositories.target_config_repo import TargetConfigRepository
from app.schemas.target import TargetUpdateRequest


class TargetService:
    """Business logic for target configuration management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.target_repo = TargetConfigRepository(db)
        self.log_repo = DailyLogRepository(db)

    async def get_targets(self, user_id: uuid.UUID) -> TargetConfig:
        """Get the current target config for a user."""
        config = await self.target_repo.get_by_user_id(user_id)
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TARGETS_NOT_CONFIGURED",
                    "message": "No targets configured. Please set your targets first.",
                },
            )
        return config

    async def update_targets(
        self, user_id: uuid.UUID, data: TargetUpdateRequest
    ) -> TargetConfig:
        """
        Update targets and propagate to today's log snapshot (FR6).

        1. Upsert target_configs row.
        2. If a daily_log exists for today, update its snapshot fields.
        All within a single transaction (managed by the session-per-request pattern).
        """
        config = await self.target_repo.upsert(
            user_id=user_id,
            calorie_target=data.calorie_target,
            protein_target=data.protein_target,
            sleep_target=data.sleep_target,
        )

        # FR6: Propagate to today's log snapshot
        today = date.today()
        await self.log_repo.update_snapshot_for_user_date(
            user_id=user_id,
            log_date=today,
            calorie_target=data.calorie_target,
            protein_target=data.protein_target,
            sleep_target=data.sleep_target,
        )

        return config
