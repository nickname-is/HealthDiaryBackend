from datetime import date
from enum import Enum as PythonEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    Float,
    String,
    Text,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .activity import Activity
    from .body_temperature import BodyTemperature
    from .refresh_token import RefreshToken
    from .sleep import Sleep
    from .water_intake import WaterIntake


class GenderEnum(PythonEnum):
    M = "M"
    F = "F"


class User(Base, TimeMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    height: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)
    chest_circumference: Mapped[float | None] = mapped_column(Float)
    waist_circumference: Mapped[float | None] = mapped_column(Float)
    hips_circumference: Mapped[float | None] = mapped_column(Float)
    gender: Mapped[GenderEnum | None] = mapped_column(Enum(GenderEnum))
    birth_date: Mapped[date | None] = mapped_column(Date)
    avatar: Mapped[str | None] = mapped_column(String(512))
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    activities: Mapped[list[Activity]] = relationship(
        "Activity", back_populates="user", cascade="all, delete-orphan"
    )
    water_intakes: Mapped[list[WaterIntake]] = relationship(
        "WaterIntake", back_populates="user", cascade="all, delete-orphan"
    )
    sleeps: Mapped[list[Sleep]] = relationship(
        "Sleep", back_populates="user", cascade="all, delete-orphan"
    )
    body_temperatures: Mapped[list[BodyTemperature]] = relationship(
        "BodyTemperature", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("height > 0", name="check_positive_height"),
        CheckConstraint("weight > 0", name="check_positive_weight"),
    )
