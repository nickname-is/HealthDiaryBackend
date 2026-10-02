from typing import TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    BigInteger,
    UUID,
    text,
    ForeignKey,
    DateTime,
    Float,
    CheckConstraint,
    UniqueConstraint,
    event,
)

from core.models.base import Base
from core.models.mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .user import User


class BodyTemperature(Base, TimeMixin):
    __tablename__ = "body_temperatures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    record_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="body_temperatures")

    __table_args__ = (
        CheckConstraint(
            "temperature_c >= 13.0 AND temperature_c <= 47.0",
            name="check_temperature_range",
        ),
        UniqueConstraint(
            "user_id",
            "record_datetime",
            name="uq_body_temperatures_user_id_record_datetime",
        ),
    )


@event.listens_for(BodyTemperature, "before_insert")
def receive_before_insert(mapper, connection, target):
    if target.record_datetime:
        # Округляем время до минут (удаляем секунды и микросекунды)
        target.record_datetime = target.record_datetime.replace(second=0, microsecond=0)
