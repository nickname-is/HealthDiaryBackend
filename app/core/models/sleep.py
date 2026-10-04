import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .user import User


class Sleep(Base, TimeMixin):
    __tablename__ = "sleeps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sleep_duration_minutes: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default=text("0")
    )
    sleep_quality: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=5, server_default=text("5")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship("User", back_populates="sleeps")

    __table_args__ = (
        CheckConstraint(
            "sleep_duration_minutes >= 0", name="check_positive_sleep_duration"
        ),
        CheckConstraint(
            "sleep_quality >= 1 AND sleep_quality <= 5",
            name="check_sleep_quality_range",
        ),
        UniqueConstraint(
            "user_id", "record_date", name="uq_sleeps_user_id_record_date"
        ),
    )
