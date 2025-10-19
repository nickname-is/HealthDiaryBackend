from typing import Optional

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from fastapi import HTTPException
from starlette import status

from core.models import EmailVerification


async def get_email_verification(session: AsyncSession, user_id: int) -> Optional[EmailVerification]:
    statement = select(EmailVerification).where(EmailVerification.user_id == user_id)
    result = await session.scalar(statement)

    return result


async def create_email_verification(
    session: AsyncSession,
    user_id: int,
    code: str,
    expire_at: datetime
) -> EmailVerification:
    verification = EmailVerification(
        user_id=user_id,
        code=code,
        expire_at=expire_at
    )
    session.add(verification)
    await session.commit()
    await session.refresh(verification)

    return verification


async def delete_email_verification(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        delete(EmailVerification).where(EmailVerification.user_id == user_id)
    )
    await session.commit()


async def increase_attempts(session: AsyncSession, user_id: int):
    verification = await get_email_verification(session=session, user_id=user_id)

    if verification.attempts + 1 >= verification.max_attempts:
        await delete_email_verification(session=session, user_id=user_id)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="There are too many requests.")

    verification.attempts += 1

    await session.commit()
    await session.refresh(verification)
