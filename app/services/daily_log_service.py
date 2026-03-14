import uuid
from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog
from app.repositories.daily_log_repo import DailyLogRepository
from app.repositories.target_config_repo import TargetConfigRepository
from app.schemas.daily_log import DailyLogRequest


class DailyLogService:
    """Business logic for daily log management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.log_repo = DailyLogRepository(db)
        self.target_repo = TargetConfigRepository(db)

    async def upsert_log(
        self,
        user_id: uuid.UUID,
        log_date: date,
        data: DailyLogRequest,
    ) -> tuple[DailyLog, bool]:
        """
        Create or update a daily log.

        Returns (log, created) where created is True if a new log was inserted.
        """
        # Validate: no future dates
        print(f"[UPSERT_LOG] user_id={user_id}, date={log_date}, data={data.model_dump(exclude_none=True)}")
        if log_date > date.today():
            print(f"[UPSERT_LOG] Rejected — future date {log_date}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "UNPROCESSABLE_ENTITY",
                    "message": "Cannot create a log for a future date.",
                },
            )

        existing = await self.log_repo.get_by_user_and_date(user_id, log_date)

        if existing is not None:
            print(f"[UPSERT_LOG] Existing log found (id={existing.id}) — updating.")
            # Update only provided fields
            update_fields = {}
            if data.calories is not None:
                update_fields["calories_actual"] = data.calories
            if data.protein is not None:
                update_fields["protein_actual"] = data.protein
            if data.sleep is not None:
                update_fields["sleep_actual"] = data.sleep
            if data.workout_completed is not None:
                update_fields["workout_completed"] = data.workout_completed
            if data.is_period_day is not None:
                update_fields["is_period_day"] = data.is_period_day

            if update_fields:
                print(f"[UPSERT_LOG] Updating fields: {list(update_fields.keys())}")
                log = await self.log_repo.update(existing, **update_fields)
            else:
                print("[UPSERT_LOG] No fields to update — returning existing log.")
                log = existing

            return log, False

        # Create new log — requires targets to be configured
        print("[UPSERT_LOG] No existing log — creating new. Fetching target config...")
        config = await self.target_repo.get_by_user_id(user_id)
        if config is None:
            print(f"[UPSERT_LOG] Targets not configured for user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TARGETS_NOT_CONFIGURED",
                    "message": "Cannot create a log without configured targets. Please set your targets first.",
                },
            )

        print(f"[UPSERT_LOG] Targets found. Creating log with snapshot.")
        log = await self.log_repo.create(
            user_id=user_id,
            date=log_date,
            calories_actual=data.calories,
            protein_actual=data.protein,
            sleep_actual=data.sleep,
            workout_completed=data.workout_completed or False,
            is_period_day=data.is_period_day or False,
            calorie_target_snapshot=config.calorie_target,
            protein_target_snapshot=config.protein_target,
            sleep_target_snapshot=config.sleep_target,
        )
        print(f"[UPSERT_LOG] New log created: id={log.id}")

        return log, True

    async def get_log(self, user_id: uuid.UUID, log_date: date) -> DailyLog:
        """Get a single daily log by date."""
        log = await self.log_repo.get_by_user_and_date(user_id, log_date)
        if log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DAILY_LOG_NOT_FOUND",
                    "message": f"No daily log found for date {log_date.isoformat()}.",
                },
            )
        print(f"[GET_LOG] Found log id={log.id}")
        return log

    async def get_logs_by_range(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[DailyLog]:
        """Get daily logs within a date range."""
        print(f"[GET_LOGS_RANGE] user_id={user_id}, start={start_date}, end={end_date}")
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": "start_date must be before or equal to end_date.",
                },
            )
        return await self.log_repo.get_by_user_and_date_range(
            user_id, start_date, end_date
        )

    async def delete_log(self, user_id: uuid.UUID, log_date: date) -> None:
        """Delete a daily log by date."""
        print(f"[DELETE_LOG] user_id={user_id}, date={log_date}")
        log = await self.log_repo.get_by_user_and_date(user_id, log_date)
        if log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DAILY_LOG_NOT_FOUND",
                    "message": f"No daily log found for date {log_date.isoformat()}.",
                },
            )
        await self.log_repo.delete(log)
        print(f"[DELETE_LOG] Deleted log id={log.id}")
