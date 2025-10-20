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
from core.schemas.token import Token, LogoutRequest, RefreshRequest
from core.schemas.user import UserRead
from core.schemas.email_verification import EmailVerification
from core.security import create_access_token, create_refresh_token

from crud import users as users_crud
from crud import refresh_tokens as refresh_crud
from crud import email_verifications as verifications_crud
from mailing.send_email import send_otp_email

from slowapi import Limiter
from slowapi.util import get_remote_address


log = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


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
            detail="Incorrect email or password",
        )

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
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified"
        )

    verification = await verifications_crud.get_email_verification(
        session=session,
        user_id=current_user.id
    )

    if verification:
        await verifications_crud.delete_email_verification(
            session=session,
            user_id=current_user.id
        )

    code = f"{random.randint(0, 100000):06d}"

    await send_otp_email(current_user.email, code)

    await verifications_crud.create_email_verification(
        session=session,
        user_id=current_user.id,
        code=code,
        expire_at=(datetime.now(timezone.utc).replace(tzinfo=None) +
                   timedelta(minutes=settings.OTP_CODE_EXPIRE_MINUTES))
    )

    return None


@router.post("/verify", response_model=UserRead)
async def verify(
    email_verification: EmailVerification,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already verified"
        )

    verification = await verifications_crud.get_email_verification(
        session=session,
        user_id=current_user.id
    )

    if verification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The verification code does not exist")

    if verification.expire_at < datetime.now(timezone.utc).replace(tzinfo=None):
        await verifications_crud.delete_email_verification(session=session, user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The code has expired")

    if email_verification.otp_code != verification.code:
        await verifications_crud.increase_attempts(session=session, user_id=current_user.id)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The code is incorrect"
        )

    user = await users_crud.verify_user(session=session, user_id=current_user.id)

    return user
