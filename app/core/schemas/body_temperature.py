from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BodyTemperatureBase(BaseModel):
    temperature_c: float = Field(
        36.6, ge=13.0, le=47.0, description="Температура тела, °C (13–47)"
    )
    record_datetime: datetime = Field(
        ..., description="Дата и время измерения (ISO формат)"
    )

    @field_validator("record_datetime", mode="after")
    @classmethod
    def round_to_minutes(cls, v: datetime) -> datetime:
        # Округляем время до минут (удаляем секунды и микросекунды)
        return v.replace(second=0, microsecond=0)


class BodyTemperatureUpsert(BodyTemperatureBase):
    pass


class BodyTemperatureRead(BodyTemperatureBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guid: UUID
