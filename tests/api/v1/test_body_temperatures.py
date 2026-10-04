from datetime import datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from tests.factories.user import create_user

MEASUREMENT_DATE = "2026-10-04"
RECORD_DATETIME = "2026-10-04T10:30:00"


async def test_create_body_temperature(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/body_temperatures",
        json={"record_datetime": RECORD_DATETIME, "temperature_c": 36.8},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["temperature_c"] == 36.8


async def test_create_body_temperature_rounds_seconds(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/body_temperatures",
        json={"record_datetime": "2026-10-04T10:30:45", "temperature_c": 36.8},
        headers=auth_headers,
    )

    assert response.status_code == 201
    record_datetime = datetime.fromisoformat(response.json()["record_datetime"])
    assert record_datetime.second == 0
    assert record_datetime.microsecond == 0


async def test_create_body_temperature_updates_same_minute(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    url = f"/api/v1/users/{user.id}/body_temperatures"

    await client.post(
        url,
        json={"record_datetime": RECORD_DATETIME, "temperature_c": 36.8},
        headers=auth_headers,
    )
    response = await client.post(
        url,
        json={"record_datetime": "2026-10-04T10:30:59", "temperature_c": 38.2},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["temperature_c"] == 38.2


async def test_create_body_temperature_out_of_range(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/body_temperatures",
        json={"record_datetime": RECORD_DATETIME, "temperature_c": 100.0},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_read_body_temperatures_for_day(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    await client.post(
        f"/api/v1/users/{user.id}/body_temperatures",
        json={"record_datetime": RECORD_DATETIME, "temperature_c": 36.8},
        headers=auth_headers,
    )
    response = await client.get(
        f"/api/v1/users/{user.id}/body_temperatures"
        f"?measurement_date={MEASUREMENT_DATE}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_read_body_temperatures_for_empty_day(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/body_temperatures?measurement_date=2020-01-01",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_read_body_temperatures_without_date(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/body_temperatures", headers=auth_headers
    )

    assert response.status_code == 422


async def test_delete_body_temperature(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    created = await client.post(
        f"/api/v1/users/{user.id}/body_temperatures",
        json={"record_datetime": RECORD_DATETIME, "temperature_c": 36.8},
        headers=auth_headers,
    )
    body_temp_guid = created.json()["guid"]

    response = await client.delete(
        f"/api/v1/users/{user.id}/body_temperatures/{body_temp_guid}",
        headers=auth_headers,
    )

    assert response.status_code == 204


async def test_delete_body_temperature_not_found(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.delete(
        f"/api/v1/users/{user.id}/body_temperatures"
        "/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_create_body_temperature_without_token(
    client: AsyncClient, user: User
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/body_temperatures",
        json={"record_datetime": RECORD_DATETIME, "temperature_c": 36.8},
    )

    assert response.status_code == 401


async def test_delete_body_temperature_of_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")
    response = await client.delete(
        f"/api/v1/users/{other_user.id}/body_temperatures"
        "/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 403
