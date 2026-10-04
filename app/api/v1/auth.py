import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, cast

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.limiter import limiter
from app.core.models import User, db_helper
from app.core.schemas.reset_password import PasswordResetRequest
from app.core.schemas.token import (
    LogoutRequest,
    RefreshRequest,
    RefreshTokenCreate,
    Token,
)
from app.core.schemas.user import UserRead, UserUpdate
from app.core.schemas.verification import (
    EmailVerification,
    EmailVerificationRequest,
    ResetPasswordVerification,
    VerificationTypes,
)
from app.core.security import create_access_token, create_refresh_token
from app.crud.refresh_tokens import refresh_tokens_crud
from app.crud.users import users_crud
from app.mailing.send_email import send_otp_email, send_otp_reset_password
from app.services.otp import (
    check_user_verified,
    consume_verification_code,
    get_user_by_email,
    issue_verification_code,
)

log = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=Token)
async def login_user(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    fingerprint: str | None = Form(None),
) -> Token:
    user = await users_crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    await check_user_verified(user)

    refresh_token = create_refresh_token()

    expire_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    await refresh_tokens_crud.create(
        session=session,
        obj_in=RefreshTokenCreate(
            user_id=user.id,
            token=refresh_token,
            expire_at=expire_at,
            fingerprint=fingerprint,
        ),
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
    refresh_token = await refresh_tokens_crud.get_by_token(
        session, token=logout_request.refresh_token
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
        )

    await refresh_tokens_crud.delete(session, refresh_token)

    return {"detail": "Logged out successfully"}


@router.post("/logout/all")
async def logout_all(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Выход со всех устройств: удаляет все refresh токены текущего пользователя.
    """
    await refresh_tokens_crud.delete_all_by_user(
        session=session, user_id=current_user.id
    )

    return {"detail": f"Logged out from all devices for user {current_user.email}"}


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    refresh_request: RefreshRequest,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> Token:
    """Обновление access/refresh пары"""
    refresh_token = await refresh_tokens_crud.get_by_token(
        session, token=refresh_request.refresh_token
    )
    fingerprint = refresh_request.fingerprint

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if refresh_token.expire_at < datetime.now(UTC).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )

    if not fingerprint or fingerprint != refresh_token.fingerprint:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Fingerprint mismatch"
        )

    user = await users_crud.get(session=session, id=refresh_token.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await check_user_verified(user)

    await refresh_tokens_crud.delete(session, refresh_token)

    new_access = create_access_token(subject=refresh_token.user_id)
    new_refresh = create_refresh_token()
    expire_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )

    await refresh_tokens_crud.create(
        session=session,
        obj_in=RefreshTokenCreate(
            user_id=refresh_token.user_id,
            token=new_refresh,
            expire_at=expire_at,
            fingerprint=fingerprint,
        ),
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
    background_tasks: BackgroundTasks,
) -> None:
    user = await get_user_by_email(
        session=session, email=email_verification_request.email
    )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already verified"
        )

    await issue_verification_code(
        user=user,
        verification_name=VerificationTypes.EMAIL_VERIFICATION,
        to_email=user.email,
        send_task=lambda **kwargs: background_tasks.add_task(send_otp_email, **kwargs),
    )

    return None


@router.post("/verify", response_model=UserRead)
async def verify(
    email_verification: EmailVerification,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> User:
    user = await get_user_by_email(session=session, email=email_verification.email)

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already verified"
        )

    await consume_verification_code(
        user=user,
        otp_code=email_verification.otp_code,
        verification_name=VerificationTypes.EMAIL_VERIFICATION,
    )

    verified_user = await users_crud.verify_user(session=session, user_id=user.id)

    return cast(User, verified_user)


@router.post("/request-reset-password")
@limiter.limit("1/minute")
async def request_reset_password(
    request: Request,
    reset_password_request: PasswordResetRequest,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    background_tasks: BackgroundTasks,
) -> None:
    user = await get_user_by_email(session=session, email=reset_password_request.email)

    await check_user_verified(user)

    await issue_verification_code(
        user=user,
        verification_name=VerificationTypes.RESET_PASSWORD,
        to_email=reset_password_request.email,
        send_task=lambda **kwargs: background_tasks.add_task(
            send_otp_reset_password, **kwargs
        ),
    )


@router.post("/reset-password")
async def reset_password(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    reset_password_verification: ResetPasswordVerification,
) -> dict:
    user = await get_user_by_email(
        session=session, email=reset_password_verification.email
    )

    await consume_verification_code(
        user=user,
        otp_code=reset_password_verification.otp_code,
        verification_name=VerificationTypes.RESET_PASSWORD,
    )

    new_password = reset_password_verification.new_password

    await users_crud.update(
        session=session,
        db_obj=user,
        obj_in=UserUpdate(password=new_password),
    )

    return {"detail": "Password reset successful!"}
