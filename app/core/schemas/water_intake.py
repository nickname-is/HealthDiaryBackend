from uuid import UUID
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class WaterIntakeBase(BaseModel):
    intake_amount: Optional[float] = 0.0

    @field_validator("intake_amount")
    @classmethod
    def non_negative(cls, v, field):
        if v is not None and v < 0:
            raise ValueError(f"{field.name} cannot be negative")
        return v


class WaterIntakeAggregate(WaterIntakeBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    start_period: date


class WaterIntakeUpsert(WaterIntakeBase):
    record_date: date
    add_to_existing: bool = False


class WaterIntakeRead(WaterIntakeBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    record_date: date
    id: Optional[int] = None
    guid: Optional[UUID] = None
