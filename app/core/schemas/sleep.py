from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SleepBase(BaseModel):
    sleep_duration: str = Field("00:00", description="Время сна в формате HH:MM")
    sleep_quality: int = Field(5, ge=1, le=5, description="Оценка качества сна (1–5)")
    notes: str | None = Field(
        None, max_length=2000, description="Заметки (до 2000 символов)"
    )
    record_date: date

    @field_validator("sleep_duration")
    @classmethod
    def validate_time(cls, v: str) -> str | None:
        if not isinstance(v, str) or ":" not in v:
            raise ValueError("sleep_duration must be in HH:MM format")
        try:
            hours, minutes = map(int, v.split(":"))
        except ValueError:
            raise ValueError("Invalid sleep_duration format") from None
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError("sleep_duration must be between 00:00 and 23:59")
        return v

    def duration_to_minutes(self) -> int:
        hours, minutes = map(int, self.sleep_duration.split(":"))
        return hours * 60 + minutes

    @staticmethod
    def minutes_to_str(minutes: int) -> str:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02}:{mins:02}"


class SleepUpsert(SleepBase):
    pass


class SleepRead(SleepBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    guid: UUID
