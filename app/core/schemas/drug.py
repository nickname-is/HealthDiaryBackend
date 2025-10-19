from typing import Optional

from pydantic import BaseModel, ConfigDict, PositiveFloat

from core.models.drug import (
    DosageUnitEnum,
    DosageTypeEnum
)


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
    name: Optional[str] = None
    dosage: Optional[PositiveFloat] = None
    dosage_unit: Optional[DosageUnitEnum] = None
    dosage_type: Optional[DosageTypeEnum] = None

    # Строгая валидация
    model_config = ConfigDict(extra="forbid")
