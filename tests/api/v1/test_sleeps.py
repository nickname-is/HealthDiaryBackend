from httpx import AsyncClient

from app.core.models import User

RECORD_DATE = "2026-10-04"


async def test_create_sleep(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/sleeps",
        json={
            "record_date": RECORD_DATE,
            "sleep_duration": "08:30",
            "sleep_quality": 4,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["sleep_duration"] == "08:30"
    assert response.json()["sleep_quality"] == 4


async def test_create_sleep_updates_existing(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    url = f"/api/v1/users/{user.id}/sleeps"

    await client.post(
        url,
        json={"record_date": RECORD_DATE, "sleep_duration": "08:30"},
        headers=auth_headers,
    )
    response = await client.post(
        url,
        json={"record_date": RECORD_DATE, "sleep_duration": "06:15"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["sleep_duration"] == "06:15"


async def test_create_sleep_with_notes(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/sleeps",
        json={
            "record_date": RECORD_DATE,
            "sleep_duration": "07:00",
            "notes": "Спал хорошо",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["notes"] == "Спал хорошо"


async def test_create_sleep_invalid_duration(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/sleeps",
        json={"record_date": RECORD_DATE, "sleep_duration": "abc"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_create_sleep_duration_out_of_range(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/sleeps",
        json={"record_date": RECORD_DATE, "sleep_duration": "25:00"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_create_sleep_invalid_quality(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/sleeps",
        json={"record_date": RECORD_DATE, "sleep_quality": 10},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_read_sleep(client: AsyncClient, user: User, auth_headers: dict) -> None:
    url = f"/api/v1/users/{user.id}/sleeps"

    await client.post(
        url,
        json={"record_date": RECORD_DATE, "sleep_duration": "08:00"},
        headers=auth_headers,
    )
    response = await client.get(
        f"{url}?record_date={RECORD_DATE}", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["sleep_duration"] == "08:00"


async def test_read_sleep_not_found(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/sleeps?record_date=2020-01-01", headers=auth_headers
    )

    assert response.status_code == 404


async def test_read_sleep_without_record_date(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(f"/api/v1/users/{user.id}/sleeps", headers=auth_headers)

    assert response.status_code == 422


async def test_create_sleep_without_token(client: AsyncClient, user: User) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/sleeps",
        json={"record_date": RECORD_DATE, "sleep_duration": "08:00"},
    )

    assert response.status_code == 401
