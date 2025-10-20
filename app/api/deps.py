from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from pydantic import ValidationError

from core import security
from core.config import settings
from core.models import db_helper, User
from core.schemas.token import TokenPayload

from crud import users as users_crud

from sqlalchemy.ext.asyncio import AsyncSession


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api.prefix}{settings.api.v1.prefix}{settings.api.v1.auth}/login"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
        token: TokenDep
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
        )

    user = await users_crud.get_user_by_id(
        session=session,
        user_id=token_data.sub
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user
