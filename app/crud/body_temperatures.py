import uuid
from datetime import datetime, date
from typing import Sequence, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models import BodyTemperature
from core.schemas.body_temperature import BodyTemperatureUpsert


async def get_body_temperature(
    session: AsyncSession,
    user_id: int,
    record_datetime: datetime
) -> Optional[BodyTemperature]:
    result = await session.scalars(
        select(BodyTemperature).where(
            BodyTemperature.user_id == user_id,
            BodyTemperature.record_datetime == record_datetime.replace(second=0, microsecond=0),
        )
    )

    return result.one_or_none()


async def get_body_temperature_by_guid(
    session: AsyncSession,
    guid: uuid.UUID,
    user_id: int,
) -> Optional[BodyTemperature]:
    result = await session.scalars(
        select(BodyTemperature).where(
            BodyTemperature.user_id == user_id,
            BodyTemperature.guid == guid,
        )
    )

    return result.one_or_none()


async def get_body_temperatures_for_day(
    session: AsyncSession,
    user_id: int,
    measurement_date: date,
) -> Sequence[BodyTemperature]:
    start = datetime.combine(measurement_date, datetime.min.time())
    end = datetime.combine(measurement_date, datetime.max.time())

    result = await session.scalars(
        select(BodyTemperature)
        .where(
            BodyTemperature.user_id == user_id,
            BodyTemperature.record_datetime.between(start, end),
        )
        .order_by(BodyTemperature.record_datetime.asc())
    )

    return result.all()


async def upsert_body_temperature(
    session: AsyncSession,
    user_id: int,
    body_temp_in: BodyTemperatureUpsert,
) -> BodyTemperature:
    body_temp = await get_body_temperature(
        session=session,
        user_id=user_id,
        record_datetime=body_temp_in.record_datetime,
    )

    if body_temp:
        body_temp.temperature_c = body_temp_in.temperature_c
    else:
        body_temp = BodyTemperature(
            user_id=user_id,
            temperature_c=body_temp_in.temperature_c,
            record_datetime=body_temp_in.record_datetime,
        )
        session.add(body_temp)

    await session.commit()
    await session.refresh(body_temp)
    return body_temp


async def delete_body_temperature(session: AsyncSession, body_temp: BodyTemperature) -> None:
    await session.delete(body_temp)
    await session.commit()
