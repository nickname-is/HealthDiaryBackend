from datetime import datetime
import uuid
from typing import TYPE_CHECKING

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
    false,
    text,
)

from .base import Base
from .mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .task_repeat import TaskRepeat
    from .drug import Drug


class Task(Base, TimeMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    all_day: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reminder_minutes: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    is_reminded: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    drug: Mapped["Drug | None"] = relationship(
        "Drug",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    repeat: Mapped["TaskRepeat | None"] = relationship(
        "TaskRepeat",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("end_datetime >= start_datetime", name="check_end_after_start"),
        CheckConstraint("reminder_minutes >= 0", name="check_non_negative_reminder"),
    )
