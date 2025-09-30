from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, ForeignKey, DateTime
from datetime import datetime

from .base import Base
from .mixins.time_mixin import TimeMixin

if TYPE_CHECKING:
    from .user import User


class RefreshToken(Base, TimeMixin):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
