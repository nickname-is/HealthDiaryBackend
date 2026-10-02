from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models.subscription_plan import SubscriptionPlan


async def get_all_plans(session: AsyncSession) -> Sequence[SubscriptionPlan]:
    result = await session.scalars(select(SubscriptionPlan))

    return result.all()


async def get_plan_by_id(
    session: AsyncSession, plan_id: int
) -> Optional[SubscriptionPlan]:
    result = await session.scalars(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    )

    return result.first()
