import logging
import uuid
from datetime import date
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
)
from starlette import status

from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_user_permission
from core.models import db_helper
from core.models.user import User
from core.schemas.body_temperature import BodyTemperatureRead, BodyTemperatureUpsert

import crud.body_temperatures as crud_body_temp


log = logging.getLogger(__name__)
router = APIRouter(tags=["BodyTemperatures"])


@router.get("/", response_model=list[BodyTemperatureRead])
async def get_body_temperatures_for_day(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    measurement_date: date = Query(..., description="Дата записи измерений температуры (YYYY-MM-DD)"),
):
    body_temperatures = await crud_body_temp.get_body_temperatures_for_day(
        session=session,
        user_id=user_id,
        measurement_date=measurement_date,
    )

    if not body_temperatures:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No body temperature measurements were found for the specified day.",
        )

    return body_temperatures


@router.post("/", response_model=BodyTemperatureRead, status_code=status.HTTP_201_CREATED)
async def create_or_update_body_temperature(
    user_id: int,
    body_temp_in: BodyTemperatureUpsert,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    body_temperature = await crud_body_temp.upsert_body_temperature(
        session=session,
        user_id=user_id,
        body_temp_in=body_temp_in,
    )

    return body_temperature


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_body_temperature(
    user_id: int,
    body_temp_guid: uuid.UUID,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    body_temperature = await crud_body_temp.get_body_temperature_by_guid(
        session=session,
        guid=body_temp_guid,
        user_id=user_id,
    )

    if not body_temperature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Body temperature measurement not found",
        )

    await crud_body_temp.delete_body_temperature(session=session, body_temp=body_temperature)
    return
