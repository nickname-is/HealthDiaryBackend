from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import SubscriptionPlan


async def create_subscription_plan(
    session: AsyncSession, **overrides: Any
) -> SubscriptionPlan:
    plan = SubscriptionPlan(
        name=overrides.pop("name", "Test Plan"),
        slug=overrides.pop("slug", "test_plan"),
        price_rub=overrides.pop("price_rub", 100),
        **overrides,
    )
    session.add(plan)
    await session.flush()

    return plan
