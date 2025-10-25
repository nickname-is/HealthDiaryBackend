import logging
from typing import Annotated, Optional
from datetime import date, timedelta
from enum import Enum as PythonEnum

from dateutil.relativedelta import relativedelta
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from starlette import status

from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_user_permission
from core.models import db_helper
from core.models.user import User
from core.schemas.activity import ActivityRead, ActivityUpsert, ActivityAggregate

import crud.activities as crud_activities


log = logging.getLogger(__name__)
router = APIRouter(tags=["Activities"])


class PeriodEnum(PythonEnum):
    WEEK = "week"
    MONTH = "month"
    SIX_MONTHS = "six_months"
    YEAR = "year"


@router.get("/", response_model=list[ActivityRead | ActivityAggregate])
async def read_activities(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    period: Optional[PeriodEnum] = Query(None, description="Предустановленный диапазон: week, month, six_months, year"),
    offset: Optional[int] = Query(0, description="Сдвиг периода (влево: -1, вправо: +1)"),
):
    if not period:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Period is required")

    today = date.today()
    ranges: list[tuple[date, date]] = []
    is_week = False

    if period == PeriodEnum.WEEK:
        start_of_week = today - timedelta(days=today.weekday()) + relativedelta(weeks=offset)
        ranges = [(start_of_week + timedelta(days=day_index), start_of_week + timedelta(days=day_index))
                  for day_index in range(7)]
        is_week = True

    elif period == PeriodEnum.MONTH:
        start_of_month = today.replace(day=1) + relativedelta(months=offset)
        current_start = start_of_month
        while current_start.month == start_of_month.month:
            current_end = current_start + timedelta(days=6)
            if current_end.month != current_start.month:
                current_end = (current_start + relativedelta(months=1)) - timedelta(days=1)
            ranges.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)

    elif period == PeriodEnum.SIX_MONTHS:
        start_month = (today.month - 1) // 6 * 6 + 1
        start_date = date(today.year, start_month, 1) + relativedelta(months=6 * offset)
        for month_index in range(6):
            month_start = start_date + relativedelta(months=month_index)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)
            ranges.append((month_start, month_end))

    elif period == PeriodEnum.YEAR:
        start_date = date(today.year, 1, 1) + relativedelta(years=offset)
        for quarter in range(4):
            quarter_start = start_date + relativedelta(months=3 * quarter)
            quarter_end = quarter_start + relativedelta(months=3) - timedelta(days=1)
            ranges.append((quarter_start, quarter_end))

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported period")

    aggregated: list[ActivityRead | ActivityAggregate] = []

    if is_week:
        all_activities = await crud_activities.get_activities_filtered(
            session=session,
            user_id=user_id,
            start_date=ranges[0][0],
            end_date=ranges[-1][1]
        )
        for start, _ in ranges:
            activity = next((activity for activity in all_activities if activity.record_date == start), None)
            aggregated.append(ActivityRead(
                id=activity.id if activity else None,
                guid=activity.guid if activity else None,
                record_date=start,
                steps=activity.steps if activity else 0,
                calories=activity.calories if activity else 0.0,
                rest_hours=activity.rest_hours if activity else 0.0,
                distance_km=activity.distance_km if activity else 0.0,
            ))
    else:
        for start, end in ranges:
            activities = await crud_activities.get_activities_filtered(
                session=session,
                user_id=user_id,
                start_date=start,
                end_date=end
            )
            aggregated.append(ActivityAggregate(
                start_period=start,
                steps=sum(activity.steps for activity in activities) if activities else 0,
                calories=sum(activity.calories for activity in activities) if activities else 0.0,
                rest_hours=sum(activity.rest_hours for activity in activities) if activities else 0.0,
                distance_km=sum(activity.distance_km for activity in activities) if activities else 0.0,
            ))

    return aggregated


@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_activity(
    user_id: int,
    activity_in: ActivityUpsert,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    activity = await crud_activities.upsert_activity(
        session=session,
        user_id=user_id,
        activity_upsert=activity_in
    )
    return activity
