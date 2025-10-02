import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.deps import CurrentUser
from core.models import db_helper
from core.schemas.user import (
    UserRead,
    UserCreate,
    UserUpdate,
)
from crud import users as users_crud


log = logging.getLogger(__name__)
router = APIRouter(tags=["Users"])


@router.get("/", response_model=list[UserRead])
async def read_users(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    return await users_crud.get_all_users(session)


@router.get("/me", response_model=UserRead)
async def read_user_me(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    user = await users_crud.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    user = await users_crud.create_user(session, user_in)
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    db_user = await users_crud.get_user_by_id(session, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await users_crud.update_user(session, db_user, user_in)


@router.delete("/{user_id}", response_model=UserRead)
async def delete_user(
    user_id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    user = await users_crud.delete_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
