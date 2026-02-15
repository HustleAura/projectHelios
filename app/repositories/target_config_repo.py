import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.target_config import TargetConfig


class TargetConfigRepository:
    """Data access layer for the target_configs table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[TargetConfig]:
        result = await self.db.execute(
            select(TargetConfig).where(TargetConfig.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        calorie_target: int,
        protein_target: int,
        sleep_target: Decimal,
    ) -> TargetConfig:
        """Create or update the target config for a user."""
        existing = await self.get_by_user_id(user_id)

        if existing is not None:
            existing.calorie_target = calorie_target
            existing.protein_target = protein_target
            existing.sleep_target = sleep_target
            await self.db.flush()
            return existing

        config = TargetConfig(
            user_id=user_id,
            calorie_target=calorie_target,
            protein_target=protein_target,
            sleep_target=sleep_target,
        )
        self.db.add(config)
        await self.db.flush()
        return config
