from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemas.subscription_plan import SubscriptionPlanRead
from core.schemas.user_subscription import UserSubscriptionRead

from api.deps import check_user_permission
from core.models import db_helper, User
from crud import user_subscriptions as user_subscriptions_crud
from crud import subscription_plans as subscription_plans_crud


router = APIRouter(tags=["Subscriptions"])


@router.get("/plans", response_model=list[SubscriptionPlanRead])
async def list_plans(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    return await subscription_plans_crud.get_all_plans(session=session)


@router.get("/current", response_model=UserSubscriptionRead)
async def get_current_subscription(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(check_user_permission)],
):
    sub = await user_subscriptions_crud.get_user_subscription(
        session=session, user_id=current_user.id
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Подписка не найдена"
        )

    return sub


@router.post("/activate/{plan_id}", response_model=UserSubscriptionRead)
async def activate_subscription(
    plan_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(check_user_permission)],
):
    plan = await subscription_plans_crud.get_plan_by_id(
        session=session, plan_id=plan_id
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )

    sub = await user_subscriptions_crud.create_user_subscription(
        session=session,
        user_id=current_user.id,
        plan=plan,
    )

    return sub
