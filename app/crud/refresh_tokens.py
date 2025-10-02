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
    result = await session.execute(
        select(RefreshToken).where(token == RefreshToken.token)
    )
    return result.scalars().first()


async def get_by_user(session: AsyncSession, user_id: int) -> Sequence[RefreshToken]:
    result = await session.execute(
        select(RefreshToken).where(user_id == RefreshToken.user_id)
    )
    return result.scalars().all()


async def delete_token(session: AsyncSession, token: RefreshToken) -> None:
    await session.delete(token)
    await session.commit()


async def delete_all_by_user(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        delete(RefreshToken).where(user_id == RefreshToken.user_id)
    )
    await session.commit()
