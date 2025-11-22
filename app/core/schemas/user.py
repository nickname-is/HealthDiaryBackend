from datetime import datetime, date
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    PositiveFloat,
    model_validator,
)

from core.models.user import GenderEnum


class UserBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    bio: Optional[str] = None
    email: EmailStr
    height: Optional[PositiveFloat] = None
    weight: Optional[PositiveFloat] = None
    chest_circumference: Optional[PositiveFloat] = None
    waist_circumference: Optional[PositiveFloat] = None
    hips_circumference: Optional[PositiveFloat] = None
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    height: Optional[PositiveFloat] = None
    weight: Optional[PositiveFloat] = None
    chest_circumference: Optional[PositiveFloat] = None
    waist_circumference: Optional[PositiveFloat] = None
    hips_circumference: Optional[PositiveFloat] = None
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    avatar: Optional[str] = None

    # Строгая валидация
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    def forbid_null_values(cls, values):
        forbid_null = ["first_name", "email", "password"]

        for key, value in values.items():
            if value is None and key in forbid_null:
                raise ValueError(f"{key} cannot be null")

        return values


class UserRead(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime