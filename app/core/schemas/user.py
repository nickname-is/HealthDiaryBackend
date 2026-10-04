import re
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    PositiveFloat,
    model_validator,
)

from app.core.models.user import GenderEnum


def _check_password_strength(password: str) -> str | None:
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one digit.")

    if not re.search(r"[\W_]", password):  # \W - любые не-алфавитные символы
        errors.append("Password must contain at least one special character.")

    if errors:
        raise ValueError("; ".join(errors))

    return password


def _validate_name(name: str) -> str | None:
    # Разрешены буквы всех языков, цифры, пробелы, апострофы, дефисы и нижние подчёркивания
    if not re.match(r"^[\w\s'-]+$", name, re.UNICODE):
        raise ValueError(
            "Name can only contain letters (any language), digits, spaces, apostrophes, hyphens, and underscores."
        )

    return name


ValidNameStr = Annotated[str, AfterValidator(_validate_name)]
StrongPasswordStr = Annotated[str, AfterValidator(_check_password_strength)]


class UserBase(BaseModel):
    first_name: ValidNameStr
    last_name: ValidNameStr | None = None
    bio: str | None = None
    email: EmailStr
    height: PositiveFloat | None = None
    weight: PositiveFloat | None = None
    chest_circumference: PositiveFloat | None = None
    waist_circumference: PositiveFloat | None = None
    hips_circumference: PositiveFloat | None = None
    gender: GenderEnum | None = None
    birth_date: date | None = None


class UserCreate(UserBase):
    password: StrongPasswordStr

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    first_name: ValidNameStr | None = None
    last_name: ValidNameStr | None = None
    bio: str | None = None
    password: StrongPasswordStr | None = None
    height: PositiveFloat | None = None
    weight: PositiveFloat | None = None
    chest_circumference: PositiveFloat | None = None
    waist_circumference: PositiveFloat | None = None
    hips_circumference: PositiveFloat | None = None
    gender: GenderEnum | None = None
    birth_date: date | None = None
    avatar: str | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def forbid_null_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        forbid_null = ["first_name", "password"]

        for key, value in values.items():
            if value is None and key in forbid_null:
                raise ValueError(f"{key} cannot be null")

        return values


class UserRead(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    avatar: str | None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
