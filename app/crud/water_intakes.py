from typing import Sequence, Optional
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.water_intake import WaterIntake
from core.schemas.water_intake import WaterIntakeUpsert


async def upsert_water_intake(
    session: AsyncSession, user_id: int, water_intake_upsert: WaterIntakeUpsert
) -> WaterIntake:
    result = await session.execute(
        select(WaterIntake).where(
            WaterIntake.user_id == user_id,
            WaterIntake.record_date == water_intake_upsert.record_date,
        )
    )
    water_intake = result.scalar_one_or_none()

    incoming_data = water_intake_upsert.model_dump(
        exclude={"add_to_existing", "record_date"}, exclude_unset=True
    )

    if water_intake:
        for field, value in incoming_data.items():
            current_value = getattr(water_intake, field, 0)
            if water_intake_upsert.add_to_existing:
                setattr(water_intake, field, current_value + value)
            else:
                setattr(water_intake, field, value)
    else:
        water_intake = WaterIntake(
            user_id=user_id,
            record_date=water_intake_upsert.record_date,
            intake_amount=water_intake_upsert.intake_amount or 0.0,
        )
        session.add(water_intake)

    await session.commit()
    await session.refresh(water_intake)
    return water_intake


async def get_water_intake(
    session: AsyncSession, user_id: int, record_date
) -> WaterIntake | None:
    result = await session.execute(
        select(WaterIntake).where(
            WaterIntake.user_id == user_id, WaterIntake.record_date == record_date
        )
    )
    return result.scalar_one_or_none()


async def get_water_intakes(
    session: AsyncSession, user_id: int
) -> Sequence[WaterIntake]:
    result = await session.execute(
        select(WaterIntake)
        .where(WaterIntake.user_id == user_id)
        .order_by(WaterIntake.record_date.desc())
    )
    return result.scalars().all()


async def get_water_intakes_filtered(
    session: AsyncSession,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
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

    result = await session.execute(query)
    return result.scalars().all()


async def delete_water_intake(session: AsyncSession, water_intake: WaterIntake):
    await session.delete(water_intake)
    await session.commit()
