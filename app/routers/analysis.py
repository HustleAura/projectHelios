from datetime import date

from fastapi import APIRouter

from app.dependencies import CurrentUser, DBSession
from app.schemas.analysis import DailyAnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.daily_log_service import DailyLogService

router = APIRouter()


@router.get("/logs/{log_date}/analysis", response_model=DailyAnalysisResponse)
async def get_daily_analysis(log_date: date, user: CurrentUser, db: DBSession):
    """Get computed performance analysis for a specific date."""
    log_service = DailyLogService(db)
    log = await log_service.get_log(user.id, log_date)
    return AnalysisService.compute(log)
