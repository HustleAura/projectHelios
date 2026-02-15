from fastapi import APIRouter

from app.dependencies import CurrentUser, DBSession
from app.schemas.target import TargetResponse, TargetUpdateRequest
from app.services.target_service import TargetService

router = APIRouter()


@router.get("/targets", response_model=TargetResponse)
async def get_targets(user: CurrentUser, db: DBSession):
    """Get the current target configuration."""
    service = TargetService(db)
    config = await service.get_targets(user.id)
    return config


@router.put("/targets", response_model=TargetResponse)
async def update_targets(
    data: TargetUpdateRequest,
    user: CurrentUser,
    db: DBSession,
):
    """Update target configuration (upsert). Also updates today's log snapshot if it exists."""
    service = TargetService(db)
    config = await service.update_targets(user.id, data)
    return config
