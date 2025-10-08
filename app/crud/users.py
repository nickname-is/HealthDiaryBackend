from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User
from core.schemas.user import UserCreate, UserUpdate
from core.security import get_hash_password, verify_password


async def get_all_users(session: AsyncSession,) -> Sequence[User]:
    stmt = select(User).order_by(User.id)
    result = await session.scalars(stmt)
    return result.all()


async def get_user_by_id(session: AsyncSession, user_id: int,) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_email(
        session: AsyncSession,
        email: str
) -> User | None:
    statement = select(User).where(email == User.email)
    result = await session.scalar(statement)

    return result


async def create_user(session: AsyncSession, user_create: UserCreate,) -> User:
    user = User(**user_create.model_dump())
    user.password = get_hash_password(user_create.password)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user: User, user_update: UserUpdate) -> User:
    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = get_hash_password(update_data["password"])

    for field, value in update_data.items():
        setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> Optional[User]:
    user = await get_user_by_id(session, user_id)
    if user is None:
        return None

    await session.delete(user)
    await session.commit()
    return user


async def authenticate(
        session: AsyncSession,
        email: str,
        password: str
) -> User | None:
    user = await get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None

    return user
