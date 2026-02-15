from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser, DBSession
from app.schemas.daily_log import DailyLogListResponse, DailyLogRequest, DailyLogResponse
from app.services.daily_log_service import DailyLogService

router = APIRouter()


@router.put("/logs/{log_date}", response_model=DailyLogResponse)
async def upsert_daily_log(
    log_date: date,
    data: DailyLogRequest,
    user: CurrentUser,
    db: DBSession,
    response: Response,
):
    """Create or update a daily log for a given date."""
    service = DailyLogService(db)
    log, created = await service.upsert_log(user.id, log_date, data)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return DailyLogResponse.from_model(log)


@router.get("/logs/{log_date}", response_model=DailyLogResponse)
async def get_daily_log(log_date: date, user: CurrentUser, db: DBSession):
    """Get a single daily log by date."""
    service = DailyLogService(db)
    log = await service.get_log(user.id, log_date)
    return DailyLogResponse.from_model(log)


@router.get("/logs", response_model=DailyLogListResponse)
async def get_daily_logs_by_range(
    user: CurrentUser,
    db: DBSession,
    start_date: date = Query(..., description="Start of date range (inclusive)."),
    end_date: date = Query(..., description="End of date range (inclusive)."),
):
    """Get daily logs within a date range."""
    service = DailyLogService(db)
    logs = await service.get_logs_by_range(user.id, start_date, end_date)
    return DailyLogListResponse(
        logs=[DailyLogResponse.from_model(log) for log in logs],
        count=len(logs),
    )


@router.delete("/logs/{log_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_log(log_date: date, user: CurrentUser, db: DBSession):
    """Delete a daily log by date."""
    service = DailyLogService(db)
    await service.delete_log(user.id, log_date)
