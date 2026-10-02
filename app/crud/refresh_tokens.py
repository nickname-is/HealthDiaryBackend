from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.models import RefreshToken


async def create_token(
    session: AsyncSession,
    user_id: int,
    token: str,
    expire_at: datetime,
    fingerprint: Optional[str] = None,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token=token,
        expire_at=expire_at,
        fingerprint=fingerprint,
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def get_by_token(session: AsyncSession, token: str) -> Optional[RefreshToken]:
    statement = select(RefreshToken).where(RefreshToken.token == token)
    result = await session.scalar(statement)

    return result


async def get_by_user(session: AsyncSession, user_id: int) -> Sequence[RefreshToken]:
    statement = select(RefreshToken).where(RefreshToken.user_id == user_id)
    result = await session.scalars(statement)

    return result.all()


async def delete_token(session: AsyncSession, token: RefreshToken) -> None:
    await session.delete(token)
    await session.commit()


async def delete_all_by_user(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await session.commit()
