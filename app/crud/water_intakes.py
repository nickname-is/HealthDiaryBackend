from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.water_intake import WaterIntake
from app.core.schemas.water_intake import WaterIntakeUpsert
from app.crud.base import CRUDBase


class CRUDWaterIntake(CRUDBase[WaterIntake, WaterIntakeUpsert, WaterIntakeUpsert]):
    @staticmethod
    async def upsert_water_intake(
        session: AsyncSession, user_id: int, water_intake_upsert: WaterIntakeUpsert
    ) -> WaterIntake:
        incoming_data = water_intake_upsert.model_dump(
            exclude={"add_to_existing", "record_date"}, exclude_unset=True
        )

        stmt = insert(WaterIntake).values(
            user_id=user_id,
            record_date=water_intake_upsert.record_date,
            intake_amount=water_intake_upsert.intake_amount or 0.0,
        )

        excluded = stmt.excluded

        if water_intake_upsert.add_to_existing:
            update_fields = {
                field: getattr(WaterIntake, field) + excluded[field]
                for field in incoming_data
            }
        else:
            update_fields = {field: excluded[field] for field in incoming_data}

        water_intake = (
            await session.scalars(
                stmt.on_conflict_do_update(
                    index_elements=["user_id", "record_date"],
                    set_=update_fields,
                ).returning(WaterIntake)
            )
        ).one()

        await session.commit()
        return water_intake

    @staticmethod
    async def get_water_intake(
        session: AsyncSession, user_id: int, record_date: date
    ) -> WaterIntake | None:
        result = await session.execute(
            select(WaterIntake).where(
                WaterIntake.user_id == user_id, WaterIntake.record_date == record_date
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_water_intakes(
        session: AsyncSession, user_id: int
    ) -> Sequence[WaterIntake]:
        result = await session.scalars(
            select(WaterIntake)
            .where(WaterIntake.user_id == user_id)
            .order_by(WaterIntake.record_date.desc())
        )
        return result.all()

    @staticmethod
    async def get_water_intakes_filtered(
        session: AsyncSession,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[WaterIntake]:
        query = select(WaterIntake).where(WaterIntake.user_id == user_id)

        if start_date and end_date:
            if start_date > end_date:
                raise ValueError("start_date не может быть больше end_date")
            query = query.where(WaterIntake.record_date.between(start_date, end_date))
        elif start_date:
            query = query.where(WaterIntake.record_date >= start_date)
        elif end_date:
            query = query.where(WaterIntake.record_date <= end_date)

        query = query.order_by(WaterIntake.record_date.desc())

        result = await session.scalars(query)
        return result.all()


water_intakes_crud = CRUDWaterIntake(WaterIntake)
