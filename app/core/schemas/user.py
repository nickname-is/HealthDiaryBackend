from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    PositiveFloat,
)

from core.models.user import GenderEnum


class UserBase(BaseModel):
    nickname: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    height: Optional[PositiveFloat] = None
    weight: Optional[PositiveFloat] = None
    gender: Optional[GenderEnum] = None
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    height: Optional[PositiveFloat] = None
    weight: Optional[PositiveFloat] = None
    gender: Optional[GenderEnum] = None
    avatar: Optional[str] = None

    # Строгая валидация
    model_config = ConfigDict(extra="forbid")


class UserRead(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    created_at: datetime
    edited_at: datetime