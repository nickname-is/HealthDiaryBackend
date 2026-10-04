from enum import Enum as PythonEnum
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

MEDIA_ROOT = Path("media").resolve()


class MediaType(PythonEnum):
    USERS = "users"


def serve_file_safe(*path_parts: str) -> FileResponse:
    for part in path_parts:
        if ".." in part or "/" in part or "\\" in part:
            raise HTTPException(status_code=400, detail="Invalid path component")

    file_path = (MEDIA_ROOT.joinpath(*path_parts)).resolve()

    if not file_path.is_relative_to(MEDIA_ROOT):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
