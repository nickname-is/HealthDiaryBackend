from httpx import AsyncClient

from app.core.models import User

RECORD_DATE = "2026-10-04"


async def test_create_water_intake(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/water_intakes",
        json={"record_date": RECORD_DATE, "intake_amount": 250},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["intake_amount"] == 250


async def test_create_water_intake_replaces_by_default(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    url = f"/api/v1/users/{user.id}/water_intakes"

    await client.post(
        url,
        json={"record_date": RECORD_DATE, "intake_amount": 250},
        headers=auth_headers,
    )
    response = await client.post(
        url,
        json={"record_date": RECORD_DATE, "intake_amount": 500},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["intake_amount"] == 500


async def test_create_water_intake_add_to_existing(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    url = f"/api/v1/users/{user.id}/water_intakes"

    await client.post(
        url,
        json={"record_date": RECORD_DATE, "intake_amount": 250},
        headers=auth_headers,
    )
    response = await client.post(
        url,
        json={
            "record_date": RECORD_DATE,
            "intake_amount": 250,
            "add_to_existing": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["intake_amount"] == 500


async def test_create_water_intake_without_amount(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/water_intakes",
        json={"record_date": RECORD_DATE},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_create_water_intake_negative_amount(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/water_intakes",
        json={"record_date": RECORD_DATE, "intake_amount": -100},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_read_water_intakes_without_period(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/water_intakes", headers=auth_headers
    )

    assert response.status_code == 400


async def test_read_water_intakes_by_day(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/water_intakes?period=day", headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 7


async def test_read_water_intakes_by_month(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/water_intakes?period=month", headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 6


async def test_read_water_intakes_by_year_not_supported(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/water_intakes?period=year", headers=auth_headers
    )

    assert response.status_code == 422


async def test_create_water_intake_without_token(
    client: AsyncClient, user: User
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/water_intakes",
        json={"record_date": RECORD_DATE, "intake_amount": 250},
    )

    assert response.status_code == 401
