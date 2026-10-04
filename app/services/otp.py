import secrets
from collections.abc import Callable

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.core.models import User
from app.core.redis_client import redis_client
from app.core.schemas.verification import VerificationTypes
from app.crud.users import users_crud


def _otp_keys(verification_name: VerificationTypes, user_id: int) -> tuple[str, str]:
    params = {"verification_type": verification_name.value, "user_id": user_id}

    return (
        settings.redis.otp_code_key.format(**params),
        settings.redis.otp_attempts_key.format(**params),
    )


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def check_user_verified(user: User) -> None:
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Verification required"
        )


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    user = await users_crud.get_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


async def issue_verification_code(
    user: User,
    verification_name: VerificationTypes,
    to_email: str,
    send_task: Callable[..., None],
) -> None:
    code_key, attempts_key = _otp_keys(verification_name, user.id)
    code = _generate_code()

    await redis_client.set(code_key, code, ex=settings.OTP_CODE_EXPIRE_MINUTES * 60)
    await redis_client.delete(attempts_key)

    send_task(
        to_email=to_email,
        otp_code=code,
        first_name=user.first_name,
    )


async def consume_verification_code(
    user: User,
    otp_code: str,
    verification_name: VerificationTypes,
) -> None:
    code_key, attempts_key = _otp_keys(verification_name, user.id)
    stored_code = await redis_client.get(code_key)

    if stored_code is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The verification code does not exist",
        )

    attempts = await redis_client.incr(attempts_key)

    if attempts == 1:
        await redis_client.expire(attempts_key, settings.OTP_CODE_EXPIRE_MINUTES * 60)

    if attempts > settings.redis.otp_max_attempts:
        await redis_client.delete(code_key, attempts_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="There are too many requests.",
        )

    if not secrets.compare_digest(str(stored_code), otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The code is incorrect"
        )

    await redis_client.delete(code_key, attempts_key)
