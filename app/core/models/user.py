from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PythonEnum
from typing import Optional, TYPE_CHECKING

from .base import Base
from .mixins.time_mixin import TimeMixin

from sqlalchemy import (
    BigInteger,
    Enum,
    Float,
    String,
    CheckConstraint,
    Boolean,
    false,
)

if TYPE_CHECKING:
    from .refresh_token import RefreshToken
    from .email_verification import EmailVerification
    from .activity import Activity
    from .water_intake import WaterIntake
    from .sleep import Sleep


class GenderEnum(PythonEnum):
    M = "M"
    F = "F"


class User(Base, TimeMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    height: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    chest_circumference: Mapped[Optional[float]] = mapped_column(Float)
    waist_circumference: Mapped[Optional[float]] = mapped_column(Float)
    hips_circumference: Mapped[Optional[float]] = mapped_column(Float)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    avatar: Mapped[Optional[str]] = mapped_column(String(512))
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    email_verification: Mapped["EmailVerification"] = relationship(
        "EmailVerification", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="user", cascade="all, delete-orphan"
    )
    water_intakes: Mapped[list["WaterIntake"]] = relationship(
        "WaterIntake", back_populates="user", cascade="all, delete-orphan"
    )
    sleeps: Mapped[list["Sleep"]] = relationship(
        "Sleep", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint('height > 0', name='check_positive_height'),
        CheckConstraint('weight > 0', name='check_positive_weight'),
    )
