from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.sql import func

from sqlalchemy import DateTime


class TimeMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
