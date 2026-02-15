import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog


class DailyLogRepository:
    """Data access layer for the daily_logs table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_and_date(
        self, user_id: uuid.UUID, log_date: date
    ) -> Optional[DailyLog]:
        result = await self.db.execute(
            select(DailyLog).where(
                DailyLog.user_id == user_id,
                DailyLog.date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_date_range(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[DailyLog]:
        result = await self.db.execute(
            select(DailyLog)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.date >= start_date,
                DailyLog.date <= end_date,
            )
            .order_by(DailyLog.date)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> DailyLog:
        log = DailyLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
        return log

    async def update(self, log: DailyLog, **kwargs) -> DailyLog:
        for key, value in kwargs.items():
            if value is not None:
                setattr(log, key, value)
        await self.db.flush()
        return log

    async def delete(self, log: DailyLog) -> None:
        await self.db.delete(log)
        await self.db.flush()

    async def update_snapshot_for_user_date(
        self,
        user_id: uuid.UUID,
        log_date: date,
        calorie_target: int,
        protein_target: int,
        sleep_target,
    ) -> Optional[DailyLog]:
        """Update the target snapshot for a specific user+date log (if it exists)."""
        log = await self.get_by_user_and_date(user_id, log_date)
        if log is None:
            return None

        log.calorie_target_snapshot = calorie_target
        log.protein_target_snapshot = protein_target
        log.sleep_target_snapshot = sleep_target
        await self.db.flush()
        return log
