from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel


class MetricAnalysis(BaseModel):
    """Analysis for a single quantitative metric."""

    actual: Optional[int | Decimal] = None
    target: int | Decimal
    delta: Optional[int | Decimal] = None
    status: Literal["met", "under", "no_data"]


class HabitIndicators(BaseModel):
    """Binary habit indicator values."""

    workout_completed: bool
    is_period_day: bool


class DailyAnalysisResponse(BaseModel):
    """Response schema for the daily analysis view."""

    date: date
    metrics: dict[str, MetricAnalysis]
    habits: HabitIndicators
