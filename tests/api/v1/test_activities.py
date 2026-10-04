from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from tests.factories.user import create_user

RECORD_DATE = "2026-10-04"


async def test_create_activity(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/activities",
        json={"record_date": RECORD_DATE, "steps": 1200},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["steps"] == 1200
    assert response.json()["record_date"] == RECORD_DATE


async def test_create_activity_replaces_by_default(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    url = f"/api/v1/users/{user.id}/activities"

    await client.post(
        url, json={"record_date": RECORD_DATE, "steps": 1200}, headers=auth_headers
    )
    response = await client.post(
        url, json={"record_date": RECORD_DATE, "steps": 500}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["steps"] == 500


async def test_create_activity_add_to_existing(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    url = f"/api/v1/users/{user.id}/activities"

    await client.post(
        url, json={"record_date": RECORD_DATE, "steps": 1200}, headers=auth_headers
    )
    response = await client.post(
        url,
        json={"record_date": RECORD_DATE, "steps": 300, "add_to_existing": True},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["steps"] == 1500


async def test_create_activity_without_values(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/activities",
        json={"record_date": RECORD_DATE},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_create_activity_negative_steps(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/activities",
        json={"record_date": RECORD_DATE, "steps": -1},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_read_activities_without_period(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/activities", headers=auth_headers
    )

    assert response.status_code == 400


async def test_read_activities_by_day(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/activities?period=day", headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 7


async def test_read_activities_by_week(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/activities?period=week", headers=auth_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_read_activities_by_month(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/activities?period=month", headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 6


async def test_read_activities_by_year(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/activities?period=year", headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 5


async def test_read_activities_invalid_period(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/activities?period=decade", headers=auth_headers
    )

    assert response.status_code == 422


async def test_create_activity_without_token(client: AsyncClient, user: User) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/activities",
        json={"record_date": RECORD_DATE, "steps": 1200},
    )

    assert response.status_code == 401


async def test_create_activity_for_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")
    response = await client.post(
        f"/api/v1/users/{other_user.id}/activities",
        json={"record_date": RECORD_DATE, "steps": 1200},
        headers=auth_headers,
    )

    assert response.status_code == 403
