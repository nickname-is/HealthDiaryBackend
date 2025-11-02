from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.sleep import Sleep
from core.schemas.sleep import SleepCreate


async def upsert_sleep(session: AsyncSession, user_id: int, sleep_in: SleepCreate) -> Sleep:
    sleep = await get_sleep(
        session=session,
        user_id=user_id,
        record_date=sleep_in.record_date
    )

    if sleep:
        sleep.sleep_duration_minutes = sleep_in.duration_to_minutes()
        sleep.sleep_quality = sleep_in.sleep_quality
        sleep.notes = sleep_in.notes
    else:
        sleep = Sleep(
            user_id=user_id,
            record_date=sleep_in.record_date,
            sleep_duration_minutes=sleep_in.duration_to_minutes(),
            sleep_quality=sleep_in.sleep_quality,
            notes=sleep_in.notes
        )
        session.add(sleep)

    await session.commit()
    await session.refresh(sleep)
    return sleep


async def get_sleep(session: AsyncSession, user_id: int, record_date: date) -> Sleep | None:
    result = await session.scalars(
        select(Sleep).where(
            Sleep.user_id == user_id,
            Sleep.record_date == record_date
        )
    )
    return result.one_or_none()