import uuid
from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base
from .mixins.time_mixin import TimeMixin

from sqlalchemy import (
    BigInteger,
    Float,
    UUID,
    Date,
    text,
    Integer,
    CheckConstraint,
    ForeignKey,
    UniqueConstraint,
)

if TYPE_CHECKING:
    from .user import User


class Activity(Base, TimeMixin):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    guid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    steps: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    calories: Mapped[float] = mapped_column(Float, default=0.0, server_default=text("0.0"))
    rest_hours: Mapped[float] = mapped_column(Float, default=0.0, server_default=text("0.0"))
    distance_km: Mapped[float] = mapped_column(Float, default=0.0, server_default=text("0.0"))

    user: Mapped["User"] = relationship("User", back_populates="activities")

    __table_args__ = (
        CheckConstraint('steps >= 0', name='check_positive_steps'),
        CheckConstraint('calories >= 0', name='check_positive_calories'),
        CheckConstraint('rest_hours >= 0', name='check_positive_rest_hours'),
        CheckConstraint('distance_km >= 0', name='check_positive_distance_km'),
        UniqueConstraint('user_id', 'record_date', name='uq_user_record_date'),
    )
