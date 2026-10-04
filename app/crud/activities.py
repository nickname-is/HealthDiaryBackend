from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.activity import Activity
from app.core.schemas.activity import ActivityUpsert
from app.crud.base import CRUDBase


class CRUDActivity(CRUDBase[Activity, ActivityUpsert, ActivityUpsert]):
    @staticmethod
    async def upsert_activity(
        session: AsyncSession, user_id: int, activity_upsert: ActivityUpsert
    ) -> Activity:
        incoming_data = activity_upsert.model_dump(
            exclude={"add_to_existing", "record_date"}, exclude_unset=True
        )

        stmt = insert(Activity).values(
            user_id=user_id,
            record_date=activity_upsert.record_date,
            steps=activity_upsert.steps or 0,
            calories=activity_upsert.calories or 0.0,
            rest_hours=activity_upsert.rest_hours or 0.0,
            distance_km=activity_upsert.distance_km or 0.0,
        )

        excluded = stmt.excluded

        if activity_upsert.add_to_existing:
            update_fields = {
                field: getattr(Activity, field) + excluded[field]
                for field in incoming_data
            }
        else:
            update_fields = {field: excluded[field] for field in incoming_data}

        activity = (
            await session.scalars(
                stmt.on_conflict_do_update(
                    index_elements=["user_id", "record_date"],
                    set_=update_fields,
                ).returning(Activity)
            )
        ).one()

        await session.commit()
        return activity

    @staticmethod
    async def get_activity(
        session: AsyncSession, user_id: int, record_date: date
    ) -> Activity | None:
        result = await session.scalars(
            select(Activity).where(
                Activity.user_id == user_id, Activity.record_date == record_date
            )
        )

        return result.one_or_none()

    @staticmethod
    async def get_activities(session: AsyncSession, user_id: int) -> Sequence[Activity]:
        result = await session.scalars(
            select(Activity)
            .where(Activity.user_id == user_id)
            .order_by(Activity.record_date.desc())
        )
        return result.all()

    @staticmethod
    async def get_activities_filtered(
        session: AsyncSession,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[Activity]:
        query = select(Activity).where(Activity.user_id == user_id)

        if start_date and end_date:
            if start_date > end_date:
                raise ValueError("start_date не может быть больше end_date")
            query = query.where(Activity.record_date.between(start_date, end_date))
        elif start_date:
            query = query.where(Activity.record_date >= start_date)
        elif end_date:
            query = query.where(Activity.record_date <= end_date)

        query = query.order_by(Activity.record_date.desc())

        result = await session.scalars(query)
        return result.all()


activities_crud = CRUDActivity(Activity)
