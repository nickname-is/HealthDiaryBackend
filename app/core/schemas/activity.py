from uuid import UUID
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ActivityBase(BaseModel):
    record_date: date
    steps: Optional[int] = 0
    calories: Optional[float] = 0.0
    rest_hours: Optional[float] = 0.0
    distance_km: Optional[float] = 0.0

    @field_validator("steps", "calories", "rest_hours", "distance_km")
    @classmethod
    def non_negative(cls, v, field):
        if v is not None and v < 0:
            raise ValueError(f"{field.name} cannot be negative")
        return v


class ActivityUpsert(ActivityBase):
    add_to_existing: bool = False


class ActivityRead(ActivityBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    guid: UUID
