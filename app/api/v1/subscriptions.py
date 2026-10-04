from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_user_permission
from app.core.models import SubscriptionPlan, User, db_helper
from app.core.schemas.subscription_plan import SubscriptionPlanRead
from app.core.schemas.user_subscription import UserSubscriptionRead
from app.crud.subscription_plans import subscription_plans_crud
from app.services.subscriptions import (
    activate_subscription,
    get_current_subscription,
)

router = APIRouter(tags=["Subscriptions"])


@router.get("/plans", response_model=list[SubscriptionPlanRead])
async def list_plans(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Sequence[SubscriptionPlan]:
    return await subscription_plans_crud.get_multi(session=session)


@router.get("/current", response_model=UserSubscriptionRead)
async def read_current_subscription(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(check_user_permission)],
) -> UserSubscriptionRead:
    return await get_current_subscription(session=session, user=current_user)


@router.post("/activate/{plan_id}", response_model=UserSubscriptionRead)
async def activate_plan(
    plan_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(check_user_permission)],
) -> UserSubscriptionRead | None:
    return await activate_subscription(
        session=session, user=current_user, plan_id=plan_id
    )
