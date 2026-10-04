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
from app.core.models.user import User
from app.core.models.water_intake import WaterIntake
from app.core.schemas.water_intake import (
    WaterIntakeAggregate,
    WaterIntakeRead,
    WaterIntakeUpsert,
)
from app.crud.water_intakes import water_intakes_crud
from app.services.periods import (
    WaterIntakePeriodEnum,
    build_ranges,
    find_by_record_date,
)

log = logging.getLogger(__name__)
router = APIRouter(tags=["WaterIntakes"])


@router.get("", response_model=list[WaterIntakeRead | WaterIntakeAggregate])
async def read_water_intakes(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    period: WaterIntakePeriodEnum | None = Query(
        None,
        description="Предустановленный диапазон: day (неделя), week (месяц), month (полугодие)",
    ),
    offset: int = Query(0, description="Сдвиг периода (влево: -1, вправо: +1)"),
) -> list[WaterIntakeRead | WaterIntakeAggregate]:
    ranges, is_day = build_ranges(period=period, offset=offset, today=date.today())

    aggregated: list[WaterIntakeRead | WaterIntakeAggregate] = []

    if is_day:
        all_water_intakes = await water_intakes_crud.get_water_intakes_filtered(
            session=session,
            user_id=user_id,
            start_date=ranges[0][0],
            end_date=ranges[-1][1],
        )
        for start, _ in ranges:
            water_intake = find_by_record_date(all_water_intakes, start)
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
            water_intakes = await water_intakes_crud.get_water_intakes_filtered(
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
) -> WaterIntake:
    water_intake = await water_intakes_crud.upsert_water_intake(
        session=session, user_id=user_id, water_intake_upsert=water_intake_in
    )
    return water_intake
