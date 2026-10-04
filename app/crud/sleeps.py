from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.sleep import Sleep
from app.core.schemas.sleep import SleepUpsert
from app.crud.base import CRUDBase


class CRUDSleep(CRUDBase[Sleep, SleepUpsert, SleepUpsert]):
    @staticmethod
    async def get_sleep(
        session: AsyncSession, user_id: int, record_date: date
    ) -> Sleep | None:
        result = await session.scalars(
            select(Sleep).where(
                Sleep.user_id == user_id, Sleep.record_date == record_date
            )
        )
        return result.one_or_none()

    @staticmethod
    async def upsert_sleep(
        session: AsyncSession, user_id: int, sleep_in: SleepUpsert
    ) -> Sleep:
        stmt = insert(Sleep).values(
            user_id=user_id,
            record_date=sleep_in.record_date,
            sleep_duration_minutes=sleep_in.duration_to_minutes(),
            sleep_quality=sleep_in.sleep_quality,
            notes=sleep_in.notes,
        )

        excluded = stmt.excluded

        update_fields = {
            "sleep_duration_minutes": excluded.sleep_duration_minutes,
            "sleep_quality": excluded.sleep_quality,
            "notes": excluded.notes,
        }

        sleep = (
            await session.scalars(
                stmt.on_conflict_do_update(
                    index_elements=["user_id", "record_date"],
                    set_=update_fields,
                ).returning(Sleep)
            )
        ).one()

        await session.commit()
        return sleep


sleeps_crud = CRUDSleep(Sleep)
