from typing import Sequence, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import User
from core.schemas.user import UserCreate, UserUpdate


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
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user: User, user_update: UserUpdate) -> User:
    update_data = user_update.model_dump(exclude_unset=True)
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
