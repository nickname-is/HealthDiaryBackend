from datetime import datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, PositiveInt, model_validator

from app.core.models.task_repeat import RepeatTypeEnum
from app.core.schemas.drug import DrugCreate, DrugRead, DrugUpdate


class TaskRepeatBase(BaseModel):
    repeat_type: RepeatTypeEnum
    repeat_interval: PositiveInt


class TaskRepeatCreate(TaskRepeatBase):
    pass


class TaskRepeatRead(TaskRepeatBase):
    id: int


class TaskBase(BaseModel):
    title: str
    all_day: bool = False
    start_datetime: datetime
    end_datetime: datetime
    reminder_minutes: int = 0
    is_completed: bool = False


class TaskCreate(TaskBase):
    guid: UUID | None = None
    drug: DrugCreate | None = None
    repeat: TaskRepeatCreate | None = None

    @model_validator(mode="after")
    def check_datetime_order(self) -> TaskCreate:
        start_datetime = self.start_datetime
        end_datetime = self.end_datetime

        if self.all_day:
            start_datetime = datetime.combine(start_datetime.date(), time.min)
            end_datetime = datetime.combine(end_datetime.date(), time.max)

        if end_datetime < start_datetime:
            raise ValueError("The end date must be after the start date.")

        return self


class TaskRead(TaskBase):
    id: int
    guid: UUID
    drug: DrugRead | None = None
    repeat: TaskRepeatRead | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    all_day: bool | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    reminder_minutes: int | None = None
    is_completed: bool | None = None
    drug: DrugUpdate | None = None
    repeat: TaskRepeatBase | None = None

    @model_validator(mode="before")
    @classmethod
    def forbid_null_values_except_allowed(
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        allowed_nulls = {"drug", "repeat"}

        for key, value in values.items():
            if value is None and key not in allowed_nulls:
                raise ValueError(f"{key} cannot be null")

        return values
