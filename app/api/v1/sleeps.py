import logging
from typing import Annotated
from datetime import date

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
from core.schemas.sleep import SleepRead, SleepCreate

import crud.sleeps as crud_sleeps


log = logging.getLogger(__name__)
router = APIRouter(tags=["Sleeps"])


@router.get("/", response_model=SleepRead)
async def read_sleep(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    record_date: date = Query(..., description="Дата записи сна (YYYY-MM-DD)"),
):
    sleep = await crud_sleeps.get_sleep(session, user_id, record_date)

    if not sleep:
        raise HTTPException(status_code=404, detail="Sleep recording not found")
    return SleepRead(
        id=sleep.id,
        guid=sleep.guid,
        record_date=sleep.record_date,
        sleep_duration=SleepCreate.minutes_to_str(sleep.sleep_duration_minutes),
        sleep_quality=sleep.sleep_quality,
        notes=sleep.notes,
    )


@router.post("/", response_model=SleepRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_sleep(
    user_id: int,
    sleep_in: SleepCreate,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    sleep = await crud_sleeps.upsert_sleep(session, user_id, sleep_in)

    return SleepRead(
        id=sleep.id,
        guid=sleep.guid,
        record_date=sleep.record_date,
        sleep_duration=SleepCreate.minutes_to_str(sleep.sleep_duration_minutes),
        sleep_quality=sleep.sleep_quality,
        notes=sleep.notes,
    )
