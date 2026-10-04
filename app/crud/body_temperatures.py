import uuid
from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import BodyTemperature
from app.core.schemas.body_temperature import BodyTemperatureUpsert
from app.crud.base import CRUDBase


class CRUDBodyTemperature(
    CRUDBase[BodyTemperature, BodyTemperatureUpsert, BodyTemperatureUpsert]
):
    @staticmethod
    async def get_body_temperature_by_guid(
        session: AsyncSession,
        guid: uuid.UUID,
        user_id: int,
    ) -> BodyTemperature | None:
        result = await session.scalars(
            select(BodyTemperature).where(
                BodyTemperature.user_id == user_id,
                BodyTemperature.guid == guid,
            )
        )

        return result.one_or_none()

    @staticmethod
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

    @staticmethod
    async def upsert_body_temperature(
        session: AsyncSession,
        user_id: int,
        body_temp_in: BodyTemperatureUpsert,
    ) -> BodyTemperature:
        stmt = insert(BodyTemperature).values(
            user_id=user_id,
            record_datetime=body_temp_in.record_datetime,
            temperature_c=body_temp_in.temperature_c,
        )

        excluded = stmt.excluded

        body_temp = (
            await session.scalars(
                stmt.on_conflict_do_update(
                    index_elements=["user_id", "record_datetime"],
                    set_={"temperature_c": excluded.temperature_c},
                ).returning(BodyTemperature)
            )
        ).one()

        await session.commit()
        return body_temp


body_temperatures_crud = CRUDBodyTemperature(BodyTemperature)
