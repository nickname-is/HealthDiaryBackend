from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.activity import Activity
from core.schemas.activity import ActivityUpsert


async def upsert_activity(session: AsyncSession, user_id: int, activity_upsert: ActivityUpsert) -> Activity:
    result = await session.execute(
        select(Activity).where(
            Activity.user_id == user_id,
            Activity.record_date == activity_upsert.record_date
        )
    )
    activity = result.scalar_one_or_none()

    incoming_data = activity_upsert.model_dump(exclude={"add_to_existing", "record_date"}, exclude_unset=True)

    if activity:
        for field, value in incoming_data.items():
            current_value = getattr(activity, field, 0)
            if activity_upsert.add_to_existing:
                setattr(activity, field, current_value + value)
            else:
                setattr(activity, field, value)
    else:
        activity = Activity(
            user_id=user_id,
            record_date=activity_upsert.record_date,
            steps=activity_upsert.steps or 0,
            calories=activity_upsert.calories or 0.0,
            rest_hours=activity_upsert.rest_hours or 0.0,
            distance_km=activity_upsert.distance_km or 0.0,
        )
        session.add(activity)

    await session.commit()
    await session.refresh(activity)
    return activity


async def get_activity(session: AsyncSession, user_id: int, record_date) -> Activity | None:
    result = await session.execute(
        select(Activity).where(
            Activity.user_id == user_id,
            Activity.record_date == record_date
        )
    )
    return result.scalar_one_or_none()


async def get_activities(session: AsyncSession, user_id: int) -> Sequence[Activity]:
    result = await session.execute(
        select(Activity).where(Activity.user_id == user_id).order_by(Activity.record_date.desc())
    )
    return result.scalars().all()


async def delete_activity(session: AsyncSession, activity: Activity):
    await session.delete(activity)
    await session.commit()
