from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.models import User, db_helper
from app.core.schemas.token import TokenPayload
from app.crud.users import users_crud

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api.prefix}{settings.api.v1.prefix}{settings.api.v1.auth}/login"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    token: TokenDep,
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {error}",
        ) from error

    user = await users_crud.get(session=session, id=token_data.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


async def check_user_permission(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access or modify this user's data.",
        )
    return current_user
