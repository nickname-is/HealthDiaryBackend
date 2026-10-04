from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.services.media import MediaType, serve_file_safe

router = APIRouter(tags=["Media"])


@router.get("/media/users/{user_id}/{filename:path}")
async def serve_user_avatar(user_id: int, filename: str) -> FileResponse:
    return serve_file_safe(MediaType.USERS.value, str(user_id), filename)
