import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import check_user_permission, get_current_user
from app.core.limiter import limiter
from app.core.models import db_helper
from app.core.models.user import User
from app.core.schemas.user import (
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.crud.users import users_crud
from app.services.user_avatar import avatar_service

log = logging.getLogger(__name__)
router = APIRouter(tags=["Users"])


@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.get("/{user_id}", response_model=UserRead, response_model_exclude={"email"})
async def read_user(
    user_id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> User:
    user = await users_crud.get(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_user(
    request: Request,
    user_in: UserCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> User:
    user = await users_crud.create(session=session, obj_in=user_in)
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> User:
    db_user = await users_crud.get(session=session, id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return await users_crud.update(session=session, db_obj=db_user, obj_in=user_in)


@router.post("/{user_id}/avatar", status_code=status.HTTP_201_CREATED)
async def upload_user_avatar(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    file: UploadFile = File(...),
) -> dict[str, str]:
    user = await users_crud.get(session=session, id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        final_name = await avatar_service.process_and_save_avatar(
            session=session, user=user, file=file
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
        ) from err

    return {
        "message": "Avatar uploaded",
        "filename": final_name,
        "url": f"users/{user_id}/{final_name}",
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> None:
    user = await users_crud.get(session=session, id=user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await users_crud.delete(session=session, db_obj=user)

    return None
