from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from tests.factories.user import create_user

START = "2026-10-04T10:00:00"
END = "2026-10-04T11:00:00"

DRUG = {
    "name": "Аспирин",
    "dosage": 500,
    "dosage_unit": "мг",
    "dosage_type": "Таблетка",
}

REPEAT = {"repeat_type": "day", "repeat_interval": 2}


async def test_create_task(client: AsyncClient, user: User, auth_headers: dict) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Принять лекарство"
    assert response.json()["guid"] is not None


async def test_create_task_with_drug(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
            "drug": DRUG,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["drug"]["name"] == "Аспирин"
    assert response.json()["drug"]["dosage"] == 500


async def test_create_task_with_repeat(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
            "repeat": REPEAT,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["repeat"]["repeat_type"] == "day"
    assert response.json()["repeat"]["repeat_interval"] == 2


async def test_create_task_all_day(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
            "all_day": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["all_day"] is True


async def test_create_task_with_invalid_dates(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": END,
            "end_datetime": START,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_create_task_with_invalid_drug_dosage(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
            "drug": {**DRUG, "dosage": -5},
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_read_tasks(client: AsyncClient, user: User, auth_headers: dict) -> None:
    await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )
    response = await client.get(f"/api/v1/users/{user.id}/tasks", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_read_tasks_empty(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(f"/api/v1/users/{user.id}/tasks", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


async def test_update_task_title(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    created = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )
    task_guid = created.json()["guid"]

    response = await client.patch(
        f"/api/v1/users/{user.id}/tasks/{task_guid}",
        json={"title": "Новое название"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Новое название"


async def test_update_task_add_drug(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    created = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )
    task_guid = created.json()["guid"]

    response = await client.patch(
        f"/api/v1/users/{user.id}/tasks/{task_guid}",
        json={"drug": DRUG},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["drug"]["name"] == "Аспирин"


async def test_update_task_not_found(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.patch(
        f"/api/v1/users/{user.id}/tasks/00000000-0000-0000-0000-000000000000",
        json={"title": "Новое название"},
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_update_task_with_null_title(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    created = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )
    task_guid = created.json()["guid"]

    response = await client.patch(
        f"/api/v1/users/{user.id}/tasks/{task_guid}",
        json={"title": None},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_delete_task(client: AsyncClient, user: User, auth_headers: dict) -> None:
    created = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )
    task_guid = created.json()["guid"]

    response = await client.delete(
        f"/api/v1/users/{user.id}/tasks/{task_guid}", headers=auth_headers
    )

    assert response.status_code == 204


async def test_delete_task_not_found(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.delete(
        f"/api/v1/users/{user.id}/tasks/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_create_task_without_token(client: AsyncClient, user: User) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
    )

    assert response.status_code == 401


async def test_create_task_for_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")
    response = await client.post(
        f"/api/v1/users/{other_user.id}/tasks",
        json={
            "title": "Принять лекарство",
            "start_datetime": START,
            "end_datetime": END,
        },
        headers=auth_headers,
    )

    assert response.status_code == 403
