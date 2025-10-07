from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PythonEnum

from .base import Base
from .mixins.time_mixin import TimeMixin

from sqlalchemy import (
    BigInteger,
    Enum,
    Float,
    String,
)


class DosageUnitEnum(PythonEnum):
    MILLIGRAM = "мг"
    MILLILITER = "мл"


class DosageTypeEnum(PythonEnum):
    CAPSULE = "Капсула"
    PILL = "Таблетка"
    POWDER = "Порошок"


class Drug(Base, TimeMixin):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[int] = mapped_column(Float, nullable=False)
    dosage_unit: Mapped[DosageUnitEnum] = mapped_column(Enum(DosageUnitEnum), nullable=False)
    dosage_type: Mapped[DosageTypeEnum] = mapped_column(Enum(DosageTypeEnum), nullable=False)
