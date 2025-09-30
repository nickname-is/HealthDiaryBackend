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
)

if TYPE_CHECKING:
    from .refresh_token import RefreshToken


class GenderEnum(PythonEnum):
    M = "M"
    F = "F"


class User(Base, TimeMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    height: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    avatar: Mapped[Optional[str]] = mapped_column(String(512))

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
