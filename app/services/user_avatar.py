import os
from uuid import uuid4

import aiofiles
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import User
from app.core.schemas.user import UserUpdate
from app.crud.users import users_crud


class AvatarService:
    def __init__(self) -> None:
        settings.media.user_media.mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def process_and_save_avatar(
        session: AsyncSession,
        user: User,
        file: UploadFile,
    ) -> str:
        if not (file.content_type or "").startswith("image/"):
            raise ValueError("Only images allowed")

        user_dir = settings.media.user_media / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)

        tmp_name = f"{uuid4()}.tmp"
        tmp_path = user_dir / tmp_name

        size = 0
        chunk_size = 64 * 1024  # 64 KB
        try:
            async with aiofiles.open(tmp_path, "wb") as f:
                while content := await file.read(chunk_size):
                    size += len(content)
                    if size > settings.media.max_avatar_size:
                        tmp_path.unlink(missing_ok=True)
                        raise ValueError(
                            f"File too large, max {settings.media.max_avatar_size} bytes"
                        )
                    await f.write(content)

            # Проверка сигнатуры
            try:
                with Image.open(tmp_path) as image:
                    kind = (image.format or "").lower()
            except UnidentifiedImageError as err:
                tmp_path.unlink(missing_ok=True)
                raise ValueError("Unsupported or invalid image type") from err

            if not kind or kind not in settings.media.allowed_image_types:
                tmp_path.unlink(missing_ok=True)
                raise ValueError("Unsupported or invalid image type")

            ext = settings.media.allowed_image_types[kind]
            final_name = f"{uuid4()}.{ext}"
            final_path = user_dir / final_name

            if user.avatar:
                old_avatar_path = user_dir / user.avatar
                if old_avatar_path.exists() and old_avatar_path.is_file():
                    old_avatar_path.unlink(missing_ok=True)

            os.rename(tmp_path, final_path)

        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            raise e

        await users_crud.update(
            session=session,
            db_obj=user,
            obj_in=UserUpdate(avatar=final_name),
        )

        return final_name


avatar_service = AvatarService()
