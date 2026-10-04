import logging
from datetime import date
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import check_user_permission
from app.core.models import db_helper
from app.core.models.user import User
from app.core.schemas.sleep import SleepRead, SleepUpsert
from app.crud.sleeps import sleeps_crud

log = logging.getLogger(__name__)
router = APIRouter(tags=["Sleeps"])


@router.get("", response_model=SleepRead)
async def read_sleep(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    record_date: date = Query(..., description="Дата записи сна (YYYY-MM-DD)"),
) -> SleepRead:
    sleep = await sleeps_crud.get_sleep(
        session=session,
        user_id=user_id,
        record_date=record_date,
    )

    if not sleep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sleep recording not found"
        )
    return SleepRead(
        id=sleep.id,
        guid=sleep.guid,
        record_date=sleep.record_date,
        sleep_duration=SleepUpsert.minutes_to_str(sleep.sleep_duration_minutes),
        sleep_quality=sleep.sleep_quality,
        notes=sleep.notes,
    )


@router.post("", response_model=SleepRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_sleep(
    user_id: int,
    sleep_in: SleepUpsert,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> SleepRead:
    sleep = await sleeps_crud.upsert_sleep(
        session=session,
        user_id=user_id,
        sleep_in=sleep_in,
    )

    return SleepRead(
        id=sleep.id,
        guid=sleep.guid,
        record_date=sleep.record_date,
        sleep_duration=SleepUpsert.minutes_to_str(sleep.sleep_duration_minutes),
        sleep_quality=sleep.sleep_quality,
        notes=sleep.notes,
    )
