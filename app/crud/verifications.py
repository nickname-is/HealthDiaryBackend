from typing import Optional

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from fastapi import HTTPException
from starlette import status

from core.models import Verification
from core.models import VerificationType


async def get_verification_type_by_name(
    session: AsyncSession, name: str
) -> Optional[VerificationType]:
    result = await session.scalars(
        select(VerificationType).where(VerificationType.name == name)
    )

    return result.one_or_none()


async def get_verification(
    session: AsyncSession, user_id: int, verification_type_id: int
) -> Optional[Verification]:
    statement = select(Verification).where(
        Verification.user_id == user_id,
        Verification.verification_type_id == verification_type_id,
    )
    result = await session.scalar(statement)

    return result


async def create_verification(
    session: AsyncSession,
    user_id: int,
    code: str,
    verification_type_id: int,
    expire_at: datetime,
) -> Verification:
    verification = Verification(
        user_id=user_id,
        code=code,
        verification_type_id=verification_type_id,
        expire_at=expire_at,
    )
    session.add(verification)
    await session.commit()
    await session.refresh(verification)

    return verification


async def delete_verification(
    session: AsyncSession, user_id: int, verification_type_id: int
) -> None:
    await session.execute(
        delete(Verification).where(
            Verification.user_id == user_id,
            Verification.verification_type_id == verification_type_id,
        )
    )
    await session.commit()


async def increase_attempts(
    session: AsyncSession, user_id: int, verification_type_id: int
):
    verification = await get_verification(
        session=session, user_id=user_id, verification_type_id=verification_type_id
    )

    if verification.attempts + 1 >= verification.max_attempts:
        await delete_verification(
            session=session, user_id=user_id, verification_type_id=verification_type_id
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="There are too many requests.",
        )

    verification.attempts += 1

    await session.commit()
    await session.refresh(verification)
