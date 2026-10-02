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
from core.schemas.water_intake import (
    WaterIntakeRead,
    WaterIntakeUpsert,
    WaterIntakeAggregate,
)

import crud.water_intakes as crud_water_intakes


log = logging.getLogger(__name__)
router = APIRouter(tags=["WaterIntakes"])


class PeriodEnum(PythonEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@router.get("", response_model=list[WaterIntakeRead | WaterIntakeAggregate])
async def read_water_intakes(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    period: Optional[PeriodEnum] = Query(
        None,
        description="Предустановленный диапазон: day (неделя), week (месяц), month (полугодие)",
    ),
    offset: Optional[int] = Query(
        0, description="Сдвиг периода (влево: -1, вправо: +1)"
    ),
):
    if not period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Period is required"
        )

    today = date.today()
    ranges: list[tuple[date, date]] = []
    is_day = False

    if period == PeriodEnum.DAY:
        start_of_week = (
            today - timedelta(days=today.weekday()) + relativedelta(weeks=offset)
        )
        ranges = [
            (
                start_of_week + timedelta(days=day_index),
                start_of_week + timedelta(days=day_index),
            )
            for day_index in range(7)
        ]
        is_day = True

    elif period == PeriodEnum.WEEK:
        start_of_month = today.replace(day=1) + relativedelta(months=offset)
        current_start = start_of_month

        while current_start.month == start_of_month.month:
            current_end = current_start + timedelta(days=6)
            if current_end.month != current_start.month:
                current_end = (current_start + relativedelta(months=1)) - timedelta(
                    days=1
                )
            ranges.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)

    elif period == PeriodEnum.MONTH:
        start_month = (today.month - 1) // 6 * 6 + 1
        start_date = date(today.year, start_month, 1) + relativedelta(months=6 * offset)

        for month_index in range(6):
            month_start = start_date + relativedelta(months=month_index)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)
            ranges.append((month_start, month_end))

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported period"
        )

    aggregated: list[WaterIntakeRead | WaterIntakeAggregate] = []

    if is_day:
        all_water_intakes = await crud_water_intakes.get_water_intakes_filtered(
            session=session,
            user_id=user_id,
            start_date=ranges[0][0],
            end_date=ranges[-1][1],
        )
        for start, _ in ranges:
            water_intake = next(
                (
                    water_intake
                    for water_intake in all_water_intakes
                    if water_intake.record_date == start
                ),
                None,
            )
            aggregated.append(
                WaterIntakeRead(
                    id=water_intake.id if water_intake else None,
                    guid=water_intake.guid if water_intake else None,
                    record_date=start,
                    intake_amount=water_intake.intake_amount if water_intake else 0.0,
                )
            )
    else:
        for start, end in ranges:
            water_intakes = await crud_water_intakes.get_water_intakes_filtered(
                session=session, user_id=user_id, start_date=start, end_date=end
            )
            aggregated.append(
                WaterIntakeAggregate(
                    start_period=start,
                    intake_amount=round(
                        sum(
                            water_intake.intake_amount for water_intake in water_intakes
                        ),
                        2,
                    )
                    if water_intakes
                    else 0.0,
                )
            )

    return aggregated


@router.post("", response_model=WaterIntakeRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_water_intake(
    user_id: int,
    water_intake_in: WaterIntakeUpsert,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    water_intake = await crud_water_intakes.upsert_water_intake(
        session=session, user_id=user_id, water_intake_upsert=water_intake_in
    )
    return water_intake
