from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BodyTemperatureBase(BaseModel):
    temperature_c: float = Field(
        36.6, ge=13.0, le=47.0, description="Температура тела, °C (13–47)"
    )
    record_datetime: datetime = Field(
        ..., description="Дата и время измерения (ISO формат)"
    )


class BodyTemperatureUpsert(BodyTemperatureBase):
    pass


class BodyTemperatureRead(BodyTemperatureBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guid: UUID
