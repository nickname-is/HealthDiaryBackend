from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.models import User
from app.core.schemas.user_subscription import UserSubscriptionRead
from app.crud.subscription_plans import subscription_plans_crud
from app.crud.user_subscriptions import user_subscriptions_crud


async def get_current_subscription(
    session: AsyncSession, user: User
) -> UserSubscriptionRead:
    sub = await user_subscriptions_crud.get_user_subscription(
        session=session, user_id=user.id
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    return sub


async def activate_subscription(
    session: AsyncSession, user: User, plan_id: int
) -> UserSubscriptionRead | None:
    plan = await subscription_plans_crud.get(session=session, id=plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    return await user_subscriptions_crud.create_user_subscription(
        session=session,
        user_id=user.id,
        plan=plan,
    )
