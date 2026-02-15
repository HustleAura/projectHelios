from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TargetUpdateRequest(BaseModel):
    """Request schema for creating/updating targets."""

    calorie_target: int = Field(..., ge=0, description="Daily calorie target.")
    protein_target: int = Field(..., ge=0, description="Daily protein target (grams).")
    sleep_target: Decimal = Field(
        ..., ge=0, le=24, description="Daily sleep target (hours)."
    )


class TargetResponse(BaseModel):
    """Response schema for target configuration."""

    calorie_target: int
    protein_target: int
    sleep_target: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}
