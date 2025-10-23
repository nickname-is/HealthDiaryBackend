from enum import Enum as PythonEnum
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Enum, Integer, CheckConstraint, ForeignKey

from .base import Base

if TYPE_CHECKING:
    from .task import Task


class RepeatTypeEnum(PythonEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TaskRepeat(Base):
    __tablename__ = "task_repeats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    repeat_type: Mapped[RepeatTypeEnum] = mapped_column(Enum(RepeatTypeEnum), nullable=False)
    repeat_interval: Mapped[int] = mapped_column(Integer, nullable=False)

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="repeat",
        uselist=False,
    )

    __table_args__ = (
        CheckConstraint("repeat_interval >= 1", name="check_positive_repeat_interval"),
    )
