import logging
from datetime import date
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import check_user_permission
from app.core.models import db_helper
from app.core.models.activity import Activity
from app.core.models.user import User
from app.core.schemas.activity import ActivityAggregate, ActivityRead, ActivityUpsert
from app.crud.activities import activities_crud
from app.services.periods import PeriodEnum, build_ranges, find_by_record_date

log = logging.getLogger(__name__)
router = APIRouter(tags=["Activities"])


@router.get("", response_model=list[ActivityRead | ActivityAggregate])
async def read_activities(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    period: PeriodEnum | None = Query(
        None,
        description="Предустановленный диапазон: day (неделя), week (месяц), month (полугодие), year (5 лет)",
    ),
    offset: int = Query(0, description="Сдвиг периода (влево: -1, вправо: +1)"),
) -> list[ActivityRead | ActivityAggregate]:
    ranges, is_day = build_ranges(period=period, offset=offset, today=date.today())

    aggregated: list[ActivityRead | ActivityAggregate] = []

    if is_day:
        all_activities = await activities_crud.get_activities_filtered(
            session=session,
            user_id=user_id,
            start_date=ranges[0][0],
            end_date=ranges[-1][1],
        )
        for start, _ in ranges:
            activity = find_by_record_date(all_activities, start)
            aggregated.append(
                ActivityRead(
                    id=activity.id if activity else None,
                    guid=activity.guid if activity else None,
                    record_date=start,
                    steps=activity.steps if activity else 0,
                    calories=activity.calories if activity else 0.0,
                    rest_hours=activity.rest_hours if activity else 0.0,
                    distance_km=activity.distance_km if activity else 0.0,
                )
            )
    else:
        for start, end in ranges:
            activities = await activities_crud.get_activities_filtered(
                session=session, user_id=user_id, start_date=start, end_date=end
            )
            aggregated.append(
                ActivityAggregate(
                    start_period=start,
                    steps=sum(activity.steps for activity in activities)
                    if activities
                    else 0,
                    calories=round(sum(activity.calories for activity in activities), 1)
                    if activities
                    else 0.0,
                    rest_hours=round(
                        sum(activity.rest_hours for activity in activities), 1
                    )
                    if activities
                    else 0.0,
                    distance_km=round(
                        sum(activity.distance_km for activity in activities), 2
                    )
                    if activities
                    else 0.0,
                )
            )

    return aggregated


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_activity(
    user_id: int,
    activity_in: ActivityUpsert,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Activity:
    activity = await activities_crud.upsert_activity(
        session=session, user_id=user_id, activity_upsert=activity_in
    )
    return activity
