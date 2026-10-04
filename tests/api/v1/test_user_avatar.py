import io
from pathlib import Path

from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.models import User
from tests.factories.user import create_user


def make_image(image_format: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format=image_format)

    return buffer.getvalue()


async def test_upload_avatar(
    client: AsyncClient, user: User, auth_headers: dict, tmp_path: Path
) -> None:
    settings.media.user_media = tmp_path

    response = await client.post(
        f"/api/v1/users/{user.id}/avatar",
        files={"file": ("avatar.png", make_image(), "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["message"] == "Avatar uploaded"
    assert (tmp_path / str(user.id) / response.json()["filename"]).exists()


async def test_upload_avatar_updates_user(
    client: AsyncClient,
    session: AsyncSession,
    user: User,
    auth_headers: dict,
    tmp_path: Path,
) -> None:
    settings.media.user_media = tmp_path

    response = await client.post(
        f"/api/v1/users/{user.id}/avatar",
        files={"file": ("avatar.png", make_image(), "image/png")},
        headers=auth_headers,
    )

    await session.refresh(user)
    assert user.avatar == response.json()["filename"]


async def test_upload_avatar_not_an_image(
    client: AsyncClient, user: User, auth_headers: dict, tmp_path: Path
) -> None:
    settings.media.user_media = tmp_path

    response = await client.post(
        f"/api/v1/users/{user.id}/avatar",
        files={"file": ("note.txt", b"just text", "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 400


async def test_upload_avatar_invalid_image(
    client: AsyncClient, user: User, auth_headers: dict, tmp_path: Path
) -> None:
    settings.media.user_media = tmp_path

    response = await client.post(
        f"/api/v1/users/{user.id}/avatar",
        files={"file": ("avatar.png", b"not an image", "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 400


async def test_upload_avatar_without_token(client: AsyncClient, user: User) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/avatar",
        files={"file": ("avatar.png", make_image(), "image/png")},
    )

    assert response.status_code == 401


async def test_upload_avatar_for_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")

    response = await client.post(
        f"/api/v1/users/{other_user.id}/avatar",
        files={"file": ("avatar.png", make_image(), "image/png")},
        headers=auth_headers,
    )

    assert response.status_code == 403
