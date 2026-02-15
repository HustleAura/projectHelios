import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class DailyLogRequest(BaseModel):
    """Request schema for creating/updating a daily log (all fields optional for partial update)."""

    calories: Optional[int] = Field(None, ge=0, description="Calories consumed.")
    protein: Optional[int] = Field(None, ge=0, description="Protein consumed (grams).")
    sleep: Optional[Decimal] = Field(
        None, ge=0, le=24, description="Hours of sleep."
    )
    workout_completed: Optional[bool] = Field(
        None, description="Whether workout was completed."
    )
    is_period_day: Optional[bool] = Field(
        None, description="Whether it's a period day."
    )


class TargetSnapshotResponse(BaseModel):
    """Nested target snapshot within a daily log response."""

    calorie_target: int
    protein_target: int
    sleep_target: Decimal


class DailyLogResponse(BaseModel):
    """Response schema for a single daily log."""

    id: uuid.UUID
    date: date
    calories: Optional[int] = None
    protein: Optional[int] = None
    sleep: Optional[Decimal] = None
    workout_completed: bool
    is_period_day: bool
    targets: TargetSnapshotResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, log) -> "DailyLogResponse":
        """Build response from a DailyLog ORM model."""
        return cls(
            id=log.id,
            date=log.date,
            calories=log.calories_actual,
            protein=log.protein_actual,
            sleep=log.sleep_actual,
            workout_completed=log.workout_completed,
            is_period_day=log.is_period_day,
            targets=TargetSnapshotResponse(
                calorie_target=log.calorie_target_snapshot,
                protein_target=log.protein_target_snapshot,
                sleep_target=log.sleep_target_snapshot,
            ),
            created_at=log.created_at,
            updated_at=log.updated_at,
        )


class DailyLogListResponse(BaseModel):
    """Response schema for a list of daily logs."""

    logs: list[DailyLogResponse]
    count: int
