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


class ActivityBase(BaseModel):
    steps: int | None = 0
    calories: float | None = 0.0
    rest_hours: float | None = 0.0
    distance_km: float | None = 0.0

    @field_validator("steps", "calories", "rest_hours", "distance_km")
    @classmethod
    def non_negative(cls, v: int | float, field: ValidationInfo) -> int | float | None:
        if v is not None and v < 0:
            raise ValueError(f"{field.field_name} cannot be negative")
        return v


class ActivityAggregate(ActivityBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    start_period: date


class ActivityUpsert(ActivityBase):
    record_date: date
    add_to_existing: bool = False

    @model_validator(mode="after")
    def require_at_least_one_value(self) -> Self:
        value_fields = {"steps", "calories", "rest_hours", "distance_km"}

        if not self.model_fields_set & value_fields:
            raise ValueError(
                "At least one of steps, calories, rest_hours, distance_km must be provided"
            )

        return self


class ActivityRead(ActivityBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    record_date: date
    id: int | None = None
    guid: UUID | None = None
