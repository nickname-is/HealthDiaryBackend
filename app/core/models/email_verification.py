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


class EmailVerification(Base, TimeMixin):
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True
    )
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    attempts: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(SmallInteger, default=5, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="email_verification")

    __table_args__ = (
        CheckConstraint('attempts >= 0', name='check_attempts_positive'),
        CheckConstraint('max_attempts > 0', name='check_max_attempts_positive'),
    )
