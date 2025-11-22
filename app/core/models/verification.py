from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.time_mixin import TimeMixin

from sqlalchemy import (
    BigInteger,
    String,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    DateTime,
)

if TYPE_CHECKING:
    from .user import User
    from .verification_type import VerificationType


class Verification(Base, TimeMixin):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True
    )
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    verification_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("verification_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attempts: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(SmallInteger, default=5, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="verifications")
    verification_type: Mapped["VerificationType"] = relationship(
        "VerificationType", back_populates="verifications"
    )

    __table_args__ = (
        CheckConstraint('attempts >= 0', name='check_attempts_positive'),
        CheckConstraint('max_attempts > 0', name='check_max_attempts_positive'),
    )
