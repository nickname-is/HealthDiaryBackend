import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Form,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.deps import CurrentUser
from core.config import settings
from core.models import db_helper
from core.schemas.token import Token
from crud import users as users_crud
from crud import refresh_tokens as refresh_crud
from core.security import create_access_token, create_refresh_token


log = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])


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
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    refresh_token: str = Form(...),
) -> dict:
    """Выход: удаление одного refresh токена"""
    refresh_token = await refresh_crud.get_by_token(session, token=refresh_token)

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    await refresh_crud.delete_token(session, refresh_token)

    return {"detail": "Logged out successfully"}


@router.post("/logout/all")
async def logout_all(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    current_user: CurrentUser,
) -> dict:
    """
    Выход со всех устройств: удаляет все refresh токены текущего пользователя.
    """
    await refresh_crud.delete_all_by_user(session=session, user_id=current_user.id)

    return {"detail": f"Logged out from all devices for user {current_user.email}"}

