from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., max_length=64)
    slug: str = Field(..., max_length=64)
    price_rub: int = Field(ge=0)


class SubscriptionPlanRead(SubscriptionPlanBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime
