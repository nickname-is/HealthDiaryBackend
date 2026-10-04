from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from app.core.security import verify_password
from tests.factories.user import create_user


async def test_get_user_me(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 200
    assert "email" in response.json()


async def test_get_user_me_without_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401


async def test_get_user_me_with_wrong_token(client: AsyncClient) -> None:
    auth_headers = {"Authorization": "Bearer 123"}
    response = await client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 403


async def test_get_excludes_email(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(f"/api/v1/users/{user.id}", headers=auth_headers)

    assert response.status_code == 200
    assert "email" not in response.json()


async def test_create_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "create_user@example.com",
            "password": "StrongPassword1!",
        },
    )

    assert response.status_code == 201


async def test_create_user_weak_pass(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "create_user@example.com",
            "password": "weak_pass",
        },
    )

    assert response.status_code == 422


async def test_create_existing_user(client: AsyncClient) -> None:
    codes = []
    for _ in range(2):
        response = await client.post(
            "/api/v1/users",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "create_user@example.com",
                "password": "StrongPassword1!",
            },
        )
        codes.append(response.status_code)

    assert codes[-1] == 409


async def test_create_user_extra_field(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "create_user@example.com",
            "password": "StrongPassword1!",
            "extra_field": "value",
        },
    )

    assert response.status_code == 422


async def test_create_user_not_valid_first_name(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={
            "first_name": "<script>alert('test');</script>",
            "last_name": "Doe",
            "email": "create_user@example.com",
            "password": "StrongPassword1!",
        },
    )

    assert response.status_code == 422


async def test_rate_limited_create_user(client: AsyncClient) -> None:
    codes = []
    for _ in range(6):
        response = await client.post(
            "/api/v1/users",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "create_user@example.com",
                "password": "StrongPassword1!",
            },
        )
        codes.append(response.status_code)

    assert codes[-1] == 429


async def test_update_first_name(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"first_name": "Jame"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Jame"


async def test_update_first_name_none(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"first_name": None},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_update_user_not_valid_first_name(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"first_name": "<script>alert('test');</script>"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_update_email(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"email": "update_email@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_update_password_hash(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    new_password = "NewPassword123!"

    response = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"password": "NewPassword123!"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    await session.refresh(user)

    assert user.password != new_password
    assert verify_password(new_password, user.password)


async def test_cannot_update_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")
    response = await client.patch(
        f"/api/v1/users/{other_user.id}",
        json={"first_name": "hacker"},
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_update_without_token(client: AsyncClient, user: User) -> None:
    response = await client.patch(
        f"/api/v1/users/{user.id}",
        json={"first_name": "John"},
    )

    assert response.status_code == 401


async def test_delete_user(client: AsyncClient, user: User, auth_headers: dict) -> None:
    response = await client.delete(
        f"/api/v1/users/{user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204


async def test_delete_non_existent_user(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    codes = []
    for _ in range(2):
        response = await client.delete(
            f"/api/v1/users/{user.id}",
            headers=auth_headers,
        )
        codes.append(response.status_code)

    assert codes[-1] == 404


async def test_delete_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")
    response = await client.delete(
        f"/api/v1/users/{other_user.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_delete_user_without_token(client: AsyncClient, user: User) -> None:
    response = await client.delete(f"/api/v1/users/{user.id}")

    assert response.status_code == 401


async def test_delete_cascade_data(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    await client.delete(
        f"/api/v1/users/{user.id}",
        headers=auth_headers,
    )
