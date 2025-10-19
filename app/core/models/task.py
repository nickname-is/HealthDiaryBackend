from datetime import datetime
import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    UUID,
    CheckConstraint,
)

from .base import Base
from .mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .task_repeat import TaskRepeat
    from .drug import Drug


class Task(Base, TimeMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reminder_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    drug_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("drugs.id", ondelete="SET NULL"),
        nullable=True,
    )
    task_repeat_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("task_repeats.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    drug: Mapped["Drug | None"] = relationship(
        "Drug",
        back_populates="task",
        uselist=False,
        cascade="all, delete",
        passive_deletes=True,
        foreign_keys=[drug_id],
    )
    repeat: Mapped["TaskRepeat | None"] = relationship(
        "TaskRepeat",
        back_populates="task",
        uselist=False,
        cascade="all, delete",
        passive_deletes=True,
        foreign_keys=[task_repeat_id],
    )

    __table_args__ = (
        CheckConstraint("end_datetime >= start_datetime", name="check_end_after_start"),
        CheckConstraint("reminder_minutes >= 0", name="check_non_negative_reminder"),
    )
