import logging
from typing import Annotated
from pathlib import Path
from uuid import uuid4
import aiofiles
import os
import imghdr

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.deps import get_current_user, check_user_permission
from core.models import db_helper
from core.models.user import User
from core.schemas.user import (
    UserRead,
    UserCreate,
    UserUpdate,
)

from slowapi import Limiter
from slowapi.util import get_remote_address

from crud import users as users_crud


log = logging.getLogger(__name__)
router = APIRouter(tags=["Users"])
limiter = Limiter(key_func=get_remote_address)

MEDIA_ROOT = Path("media")
USER_MEDIA = MEDIA_ROOT / "users"
USER_MEDIA.mkdir(parents=True, exist_ok=True)

EXT_MAP = {
    "jpeg": "jpg",
    "png": "png",
    "gif": "gif",
    "webp": "webp",
}

MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("/", response_model=list[UserRead])
async def read_users(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    return await users_crud.get_all_users(session)


@router.get("/me", response_model=UserRead)
async def read_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/{user_id}", response_model=UserRead, response_model_exclude={"email"})
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
@limiter.limit("5/minute")
async def create_user(
    request: Request,
    user_in: UserCreate,
    session: Annotated[
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
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    db_user = await users_crud.get_user_by_id(session, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await users_crud.update_user(session, db_user, user_in)


@router.post("/{user_id}/avatar", status_code=status.HTTP_201_CREATED)
async def upload_user_avatar(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    file: UploadFile = File(...),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images allowed")

    user = await users_crud.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dir = USER_MEDIA / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    tmp_name = f"{uuid4()}.tmp"
    tmp_path = user_dir / tmp_name

    size = 0
    chunk_size = 64 * 1024  # 64 KB
    async with aiofiles.open(tmp_path, "wb") as f:
        while content := await file.read(chunk_size):
            size += len(content)
            if size > MAX_AVATAR_SIZE:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large, max {MAX_AVATAR_SIZE} bytes"
                )
            await f.write(content)

    # Проверка сигнатуры
    kind = imghdr.what(tmp_path)
    if not kind or kind not in EXT_MAP:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Unsupported image type")

    ext = EXT_MAP[kind]
    final_name = f"{uuid4()}.{ext}"
    final_path = user_dir / final_name

    if user.avatar:
        old_avatar_path = user_dir / user.avatar
        if old_avatar_path.exists() and old_avatar_path.is_file():
            old_avatar_path.unlink(missing_ok=True)

    os.rename(tmp_path, final_path)

    await users_crud.update_user(
        session=session,
        user=user,
        user_update=UserUpdate(avatar=final_name),
    )

    return {
        "message": "Avatar uploaded",
        "filename": final_name,
        "url": f"users/{user_id}/{final_name}",
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    user = await users_crud.delete_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"detail": "User deleted"}
