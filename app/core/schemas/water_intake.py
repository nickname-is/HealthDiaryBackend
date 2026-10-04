from datetime import date
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)


class WaterIntakeBase(BaseModel):
    intake_amount: float | None = 0.0

    @field_validator("intake_amount")
    @classmethod
    def non_negative(cls, v: float, field: ValidationInfo) -> float | None:
        if v is not None and v < 0:
            raise ValueError(f"{field.field_name} cannot be negative")
        return v


class WaterIntakeAggregate(WaterIntakeBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    start_period: date


class WaterIntakeUpsert(WaterIntakeBase):
    record_date: date
    add_to_existing: bool = False

    @model_validator(mode="after")
    def require_at_least_one_value(self) -> Self:
        if "intake_amount" not in self.model_fields_set:
            raise ValueError("intake_amount must be provided")

        return self


class WaterIntakeRead(WaterIntakeBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    record_date: date
    id: int | None = None
    guid: UUID | None = None
