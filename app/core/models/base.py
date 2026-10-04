from typing import TYPE_CHECKING

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped

from app.core.config import settings


class Base(DeclarativeBase):
    __abstract__ = True

    if TYPE_CHECKING:
        id: Mapped[int]

    metadata = MetaData(
        naming_convention=settings.db.naming_convention,
    )
