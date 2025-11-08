from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Integer, text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .mixins.time_mixin import TimeMixin
from .base import Base

if TYPE_CHECKING:
    from .user_subscription import UserSubscription


class SubscriptionPlan(Base, TimeMixin):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    price_rub: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    user_subscription: Mapped["UserSubscription"] = relationship(
        "UserSubscription", back_populates="subscription_plan", cascade="all, delete"
    )

    __table_args__ = (
        CheckConstraint("price_rub >= 0", name="ck_plan_price_non_negative"),
    )
