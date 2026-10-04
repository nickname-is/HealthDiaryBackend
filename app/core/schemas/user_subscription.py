from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.schemas.subscription_plan import SubscriptionPlanRead


class UserSubscriptionBase(BaseModel):
    plan_id: int


class UserSubscriptionRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    subscription_plan: SubscriptionPlanRead
    start_date: datetime
    end_date: datetime | None
    is_active: bool
