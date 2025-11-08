from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from core.schemas.subscription_plan import SubscriptionPlanRead


class UserSubscriptionBase(BaseModel):
    plan_id: int


class UserSubscriptionRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    subscription_plan: SubscriptionPlanRead
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
