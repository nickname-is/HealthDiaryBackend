from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User
from tests.factories.subscription_plan import create_subscription_plan
from tests.factories.user import create_user


async def test_list_plans_empty(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/subscriptions/plans", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_list_plans(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    await create_subscription_plan(session=session, name="Без рекламы", slug="no_ads")

    response = await client.get(
        f"/api/v1/users/{user.id}/subscriptions/plans", headers=auth_headers
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["slug"] == "no_ads"


async def test_current_subscription_not_found(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.get(
        f"/api/v1/users/{user.id}/subscriptions/current", headers=auth_headers
    )

    assert response.status_code == 404


async def test_activate_subscription(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    plan = await create_subscription_plan(
        session=session, name="Без рекламы", slug="no_ads"
    )

    response = await client.post(
        f"/api/v1/users/{user.id}/subscriptions/activate/{plan.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["subscription_plan"]["slug"] == "no_ads"
    assert response.json()["is_active"] is True


async def test_activate_subscription_then_current(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    plan = await create_subscription_plan(
        session=session, name="Без рекламы", slug="no_ads"
    )

    await client.post(
        f"/api/v1/users/{user.id}/subscriptions/activate/{plan.id}",
        headers=auth_headers,
    )
    response = await client.get(
        f"/api/v1/users/{user.id}/subscriptions/current", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["subscription_plan"]["slug"] == "no_ads"


async def test_activate_subscription_plan_not_found(
    client: AsyncClient, user: User, auth_headers: dict
) -> None:
    response = await client.post(
        f"/api/v1/users/{user.id}/subscriptions/activate/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_list_plans_does_not_require_token(
    client: AsyncClient, user: User
) -> None:
    response = await client.get(f"/api/v1/users/{user.id}/subscriptions/plans")

    assert response.status_code == 200


async def test_activate_subscription_for_other_user(
    client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict
) -> None:
    other_user = await create_user(session=session, email="other@example.com")
    plan = await create_subscription_plan(
        session=session, name="Без рекламы", slug="no_ads"
    )

    response = await client.post(
        f"/api/v1/users/{other_user.id}/subscriptions/activate/{plan.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403
