from typing import Optional, TYPE_CHECKING
from enum import Enum as PythonEnum

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.time_mixin import TimeMixin

from sqlalchemy import (
    BigInteger,
    String,
)

if TYPE_CHECKING:
    from .verification import Verification


class VerificationTypes(PythonEnum):
    EMAIL_VERIFICATION = "email_verification"
    RESET_PASSWORD = "reset_password"


class VerificationType(Base, TimeMixin):
    __tablename__ = "verification_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[int] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    verifications: Mapped["Verification"] = relationship(
        "Verification", back_populates="verification_type"
    )
