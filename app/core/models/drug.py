from enum import Enum as PythonEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Enum,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .task import Task


class DosageUnitEnum(PythonEnum):
    MILLIGRAM = "мг"
    GRAM = "г"
    MILLILITER = "мл"
    MICROGRAM = "мкг"
    UNIT = "МЕ"  # Международная единица
    PIECE = "шт"
    DROP = "капля"
    SPRAY = "распыление"
    TABLESPOON = "ст.л."
    TEASPOON = "ч.л."


class DosageTypeEnum(PythonEnum):
    CAPSULE = "Капсула"
    PILL = "Таблетка"
    POWDER = "Порошок"
    AMPOULE = "Ампула"
    SOLUTION = "Раствор"
    SUSPENSION = "Суспензия"
    CREAM = "Крем"
    OINTMENT = "Мазь"
    GEL = "Гель"
    SUPPOSITORY = "Суппозитория"
    SPRAY = "Спрей"
    DROP = "Капли"
    FOAM = "Пена"
    PATCH = "Пластырь"
    INHALER = "Ингалятор"


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[float] = mapped_column(Float, nullable=False)
    dosage_unit: Mapped[DosageUnitEnum] = mapped_column(
        Enum(DosageUnitEnum), nullable=False
    )
    dosage_type: Mapped[DosageTypeEnum] = mapped_column(
        Enum(DosageTypeEnum), nullable=False
    )

    task: Mapped[Task] = relationship(
        "Task",
        back_populates="drug",
        uselist=False,
    )

    __table_args__ = (CheckConstraint("dosage > 0", name="check_positive_dosage"),)
