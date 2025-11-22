import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import random

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Form,
    Request,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.deps import get_current_user
from core.config import settings
from core.models import db_helper, User
from core.models.verification_type import VerificationTypes
from core.schemas.reset_password import PasswordResetRequest
from core.schemas.token import Token, LogoutRequest, RefreshRequest
from core.schemas.user import UserRead, UserUpdate
from core.schemas.verification import EmailVerification, ResetPasswordVerification, EmailVerificationRequest
from core.security import create_access_token, create_refresh_token

from crud import users as users_crud
from crud import refresh_tokens as refresh_crud
from crud import verifications as verifications_crud
from mailing.send_email import send_otp_email, send_otp_reset_password

from slowapi import Limiter
from slowapi.util import get_remote_address


log = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


async def verify_otp_code(session: AsyncSession, user_id: int, otp_code: str, verification_type_id: int):
    verification = await verifications_crud.get_verification(
        session=session,
        user_id=user_id,
        verification_type_id=verification_type_id,
    )

    if verification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The verification code does not exist")

    if verification.expire_at < datetime.now(timezone.utc):
        await verifications_crud.delete_verification(
            session=session,
            user_id=user_id,
            verification_type_id=verification_type_id,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The code has expired")

    if otp_code != verification.code:
        await verifications_crud.increase_attempts(
            session=session,
            user_id=user_id,
            verification_type_id=verification_type_id,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The code is incorrect")


async def check_user_verified(user: User):
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification required")


async def get_verification_type_id(
    session: AsyncSession,
    verification_name: VerificationTypes
) -> Optional[int]:
    verification_type = await verifications_crud.get_verification_type_by_name(
        session=session,
        name=verification_name.value,
    )

    if not verification_type:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification type ({verification_name.value}) not found. Please contact support."
        )

    return verification_type.id


@router.post("/login", response_model=Token)
async def login_user(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    fingerprint: Optional[str] = Form(None),
) -> Token:
    user = await users_crud.authenticate(
        session=session,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    await check_user_verified(user)

    refresh_token = create_refresh_token()

    expire_at = (datetime.now(timezone.utc).replace(tzinfo=None) +
                 timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    await refresh_crud.create_token(
        session=session,
        user_id=user.id,
        token=refresh_token,
        expire_at=expire_at,
        fingerprint=fingerprint,
    )

    token = Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=refresh_token,
    )

    return token


@router.post("/logout")
async def logout(
    logout_request: LogoutRequest,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> dict:
    """Выход: удаление одного refresh токена"""
    refresh_token = await refresh_crud.get_by_token(session, token=logout_request.refresh_token)

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    await refresh_crud.delete_token(session, refresh_token)

    return {"detail": "Logged out successfully"}


@router.post("/logout/all")
async def logout_all(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Выход со всех устройств: удаляет все refresh токены текущего пользователя.
    """
    await refresh_crud.delete_all_by_user(session=session, user_id=current_user.id)

    return {"detail": f"Logged out from all devices for user {current_user.email}"}


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    refresh_request: RefreshRequest,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Token:
    """Обновление access/refresh пары"""
    refresh_token = await refresh_crud.get_by_token(session, token=refresh_request.refresh_token)
    fingerprint = refresh_request.fingerprint

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await users_crud.get_user_by_id(session=session, user_id=refresh_token.user_id)

    await check_user_verified(user)

    # Удаляем старый refresh токен
    await refresh_crud.delete_token(session, refresh_token)

    # Проверяем срок жизни
    if refresh_token.expire_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # Проверяем fingerprint
    if fingerprint != refresh_token.fingerprint:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Fingerprint mismatch")

    # Создаём новую пару
    new_access = create_access_token(subject=refresh_token.user_id)
    new_refresh = create_refresh_token()
    expire_at = (datetime.now(timezone.utc).replace(tzinfo=None) +
                 timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))

    await refresh_crud.create_token(
        session=session,
        user_id=refresh_token.user_id,
        token=new_refresh,
        expire_at=expire_at,
        fingerprint=fingerprint,
    )

    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
    )


@router.post("/request-verify")
@limiter.limit("1/minute")
async def request_verify(
    request: Request,
    email_verification_request: EmailVerificationRequest,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    user = await users_crud.get_user_by_email(session=session, email=email_verification_request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified"
        )

    verification_type_id = await get_verification_type_id(
        session=session,
        verification_name=VerificationTypes.EMAIL_VERIFICATION,
    )

    verification = await verifications_crud.get_verification(
        session=session,
        user_id=user.id,
        verification_type_id=verification_type_id
    )

    if verification:
        await verifications_crud.delete_verification(
            session=session,
            user_id=user.id,
            verification_type_id=verification_type_id
        )

    code = f"{random.randint(0, 999999):06d}"

    await send_otp_email(to_email=user.email, otp_code=code, first_name=user.first_name)

    await verifications_crud.create_verification(
        session=session,
        user_id=user.id,
        code=code,
        verification_type_id=verification_type_id,
        expire_at=(datetime.now(timezone.utc).replace(tzinfo=None) +
                   timedelta(minutes=settings.OTP_CODE_EXPIRE_MINUTES))
    )

    return None


@router.post("/verify", response_model=UserRead)
async def verify(
    email_verification: EmailVerification,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    user = await users_crud.get_user_by_email(session=session, email=email_verification.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified"
        )

    verification_type_id = await get_verification_type_id(
        session=session,
        verification_name=VerificationTypes.EMAIL_VERIFICATION,
    )

    await verify_otp_code(
        session=session,
        user_id=user.id,
        otp_code=email_verification.otp_code,
        verification_type_id=verification_type_id,
    )

    await verifications_crud.delete_verification(
        session=session,
        user_id=user.id,
        verification_type_id=verification_type_id,
    )

    user = await users_crud.verify_user(session=session, user_id=user.id)

    return user


@router.post("/request-reset-password")
@limiter.limit("1/minute")
async def request_reset_password(
    request: Request,
    reset_password_request: PasswordResetRequest,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    user = await users_crud.get_user_by_email(session=session, email=reset_password_request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await check_user_verified(user)

    verification_type_id = await get_verification_type_id(
        session=session,
        verification_name=VerificationTypes.RESET_PASSWORD,
    )

    code = f"{random.randint(0, 999999):06d}"

    await verifications_crud.create_verification(
        session=session,
        user_id=user.id,
        code=code,
        verification_type_id=verification_type_id,
        expire_at=(datetime.now(timezone.utc).replace(tzinfo=None) +
                   timedelta(minutes=settings.OTP_CODE_EXPIRE_MINUTES))
    )

    await send_otp_reset_password(to_email=reset_password_request.email, otp_code=code, first_name=user.first_name)


@router.post("/reset-password")
async def reset_password(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    reset_password_verification: ResetPasswordVerification,
) -> dict:
    user = await users_crud.get_user_by_email(session=session, email=reset_password_verification.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    verification_type_id = await get_verification_type_id(
        session=session,
        verification_name=VerificationTypes.RESET_PASSWORD,
    )

    await verify_otp_code(
        session=session,
        user_id=user.id,
        otp_code=reset_password_verification.otp_code,
        verification_type_id=verification_type_id,
    )

    new_password = reset_password_verification.new_password
    users_crud.check_password_strength(new_password)

    await users_crud.update_user(
        session=session,
        user=user,
        user_update=UserUpdate(password=new_password),
    )

    await verifications_crud.delete_verification(
        session=session,
        user_id=user.id,
        verification_type_id=verification_type_id,
    )

    return {"detail": "Password reset successful!"}
