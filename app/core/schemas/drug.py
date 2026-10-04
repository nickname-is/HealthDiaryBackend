
from pydantic import BaseModel, ConfigDict, PositiveFloat

from app.core.models.drug import DosageTypeEnum, DosageUnitEnum


class DrugBase(BaseModel):
    name: str
    dosage: PositiveFloat
    dosage_unit: DosageUnitEnum
    dosage_type: DosageTypeEnum


class DrugCreate(DrugBase):
    pass


class DrugRead(DrugBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int


class DrugUpdate(BaseModel):
    name: str | None = None
    dosage: PositiveFloat | None = None
    dosage_unit: DosageUnitEnum | None = None
    dosage_type: DosageTypeEnum | None = None

    # Строгая валидация
    model_config = ConfigDict(extra="forbid")
