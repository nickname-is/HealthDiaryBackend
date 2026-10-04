import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .user import User


class WaterIntake(Base, TimeMixin):
    __tablename__ = "water_intakes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    intake_amount: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default=text("0.0")
    )

    user: Mapped[User] = relationship("User", back_populates="water_intakes")

    __table_args__ = (
        CheckConstraint("intake_amount >= 0", name="check_positive_intake_amount"),
        UniqueConstraint(
            "user_id", "record_date", name="uq_water_intakes_user_id_record_date"
        ),
    )
