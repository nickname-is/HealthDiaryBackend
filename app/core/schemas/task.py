from datetime import datetime
from typing import Optional
from pydantic import BaseModel, PositiveInt, model_validator
from uuid import UUID

from core.schemas.drug import DrugCreate, DrugRead, DrugUpdate
from core.models.task_repeat import RepeatTypeEnum


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
    guid: Optional[UUID] = None
    drug: Optional[DrugCreate] = None
    repeat: Optional[TaskRepeatCreate] = None


class TaskRead(TaskBase):
    id: int
    guid: UUID
    drug: Optional[DrugRead] = None
    repeat: Optional[TaskRepeatRead] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    all_day: Optional[bool] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    reminder_minutes: Optional[int] = None
    is_completed: Optional[bool] = None
    drug: Optional[DrugUpdate] = None
    repeat: Optional[TaskRepeatBase] = None

    @model_validator(mode="before")
    def forbid_null_values_except_allowed(cls, values):
        allowed_nulls = {"drug", "repeat"}

        for key, value in values.items():
            if value is None and key not in allowed_nulls:
                raise ValueError(f"{key} cannot be null")

        return values
