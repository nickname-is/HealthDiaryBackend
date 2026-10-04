from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models.subscription_plan import SubscriptionPlan
from app.core.models.user_subscription import UserSubscription
from app.core.schemas.user_subscription import (
    UserSubscriptionBase,
    UserSubscriptionRead,
)
from app.crud.base import CRUDBase


class CRUDUserSubscription(
    CRUDBase[UserSubscription, UserSubscriptionBase, UserSubscriptionBase]
):
    @staticmethod
    async def get_user_subscription(
        session: AsyncSession, user_id: int
    ) -> UserSubscriptionRead | None:
        result = await session.scalars(
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id)
            .options(selectinload(UserSubscription.subscription_plan))
        )

        subscription = result.one_or_none()

        return (
            UserSubscriptionRead.model_validate(subscription) if subscription else None
        )

    async def create_user_subscription(
        self,
        session: AsyncSession,
        user_id: int,
        plan: SubscriptionPlan,
        months: int = 1,
    ) -> UserSubscriptionRead | None:
        result = await session.scalars(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        subscription = result.first()

        if subscription:
            await self.delete(session=session, db_obj=subscription)

        new_sub = UserSubscription(
            user_id=user_id,
            plan_id=plan.id,
            start_date=datetime.now(tz=UTC),
            end_date=datetime.now(tz=UTC) + timedelta(days=30 * months),
        )
        session.add(new_sub)
        await session.commit()
        await session.refresh(new_sub)

        return await self.get_user_subscription(session=session, user_id=user_id)


user_subscriptions_crud = CRUDUserSubscription(UserSubscription)
