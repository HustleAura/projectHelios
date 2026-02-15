import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: uuid.UUID
    phone_number: str
    created_at: datetime

    model_config = {"from_attributes": True}
