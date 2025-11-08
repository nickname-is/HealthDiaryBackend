from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .mixins.time_mixin import TimeMixin
from .base import Base

if TYPE_CHECKING:
    from .subscription_plan import SubscriptionPlan


class UserSubscription(Base, TimeMixin):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    plan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("subscription_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    subscription_plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", back_populates="user_subscription"
    )

    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="check_end_date_after_start_date"
        ),
    )

    @hybrid_property
    def is_active(self) -> bool:
        return self.end_date is None or self.end_date >= datetime.now(tz=timezone.utc)
