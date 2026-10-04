from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.core.security import get_hash_password

DEFAULT_PASSWORD = "StrongPassword!123"


async def create_user(
    session: AsyncSession, password: str = DEFAULT_PASSWORD, **overrides: Any
) -> User:
    user = User(
        first_name="John",
        last_name="Smith",
        email=overrides.pop("email", "test@example.com"),
        password=get_hash_password(password),
        is_verified=True,
        **overrides,
    )
    session.add(user)
    await session.flush()

    return user
