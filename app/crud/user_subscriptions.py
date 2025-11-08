from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.models.user_subscription import UserSubscription
from core.models.subscription_plan import SubscriptionPlan
from core.schemas.user_subscription import UserSubscriptionRead


async def get_user_subscription(session: AsyncSession, user_id: int) -> Optional[UserSubscriptionRead]:
    result = await session.scalars(
        select(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .options(selectinload(UserSubscription.subscription_plan))
    )

    return result.one_or_none()


async def delete_user_subscription(session: AsyncSession, user_subscription: UserSubscription) -> None:
    await session.delete(user_subscription)
    await session.commit()


async def create_user_subscription(
    session: AsyncSession,
    user_id: int,
    plan: SubscriptionPlan,
    months: int = 1
) -> Optional[UserSubscriptionRead]:
    existing = await session.scalars(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )
    subscription = existing.first()

    if existing:
        await delete_user_subscription(session=session, user_subscription=subscription)

    new_sub = UserSubscription(
        user_id=user_id,
        plan_id=plan.id,
        start_date=datetime.now(tz=timezone.utc),
        end_date=datetime.now(tz=timezone.utc) + timedelta(days=30 * months)
    )
    session.add(new_sub)
    await session.commit()
    await session.refresh(new_sub)

    return await get_user_subscription(session=session, user_id=user_id)
