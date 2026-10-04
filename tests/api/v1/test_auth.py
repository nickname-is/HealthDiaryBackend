from typing import Any, cast

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import auth as auth_module
from app.core.config import settings
from app.core.models import User
from app.core.redis_client import redis_client
from app.core.schemas.verification import VerificationTypes
from app.core.security import verify_password
from tests.factories.user import DEFAULT_PASSWORD, create_user

EMAIL_VERIFICATION = VerificationTypes.EMAIL_VERIFICATION
RESET_PASSWORD = VerificationTypes.RESET_PASSWORD
FINGERPRINT = "test-device"


@pytest.fixture(autouse=True)
def mock_email(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_send(to_email: str, otp_code: str, first_name: str) -> None:
        pass

    monkeypatch.setattr(auth_module, "send_otp_email", fake_send)
    monkeypatch.setattr(auth_module, "send_otp_reset_password", fake_send)


@pytest_asyncio.fixture
async def unverified_user(session: AsyncSession) -> User:
    user = await create_user(session=session, email="unverified@example.com")
    user.is_verified = False
    await session.flush()

    return user


async def otp_code(verification_type: VerificationTypes, user_id: int) -> str | None:
    key = settings.redis.otp_code_key.format(
        verification_type=verification_type.value, user_id=user_id
    )

    return cast(str | None, await redis_client.get(key))


async def login(
    client: AsyncClient, email: str, password: str, fingerprint: str | None = None
) -> dict[str, Any]:
    data = {"username": email, "password": password}
    if fingerprint is not None:
        data["fingerprint"] = fingerprint

    response = await client.post("/api/v1/auth/login", data=data)

    return dict(response.json())


async def test_login(client: AsyncClient, user: User) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_login_wrong_password(client: AsyncClient, user: User) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "WrongPassword1!"},
    )

    assert response.status_code == 400


async def test_login_unverified_user(
    client: AsyncClient, unverified_user: User
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": unverified_user.email, "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 403


async def test_refresh(client: AsyncClient, user: User) -> None:
    tokens = await login(client, user.email, DEFAULT_PASSWORD, FINGERPRINT)

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"], "fingerprint": FINGERPRINT},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_refresh_without_fingerprint(client: AsyncClient, user: User) -> None:
    tokens = await login(client, user.email, DEFAULT_PASSWORD, FINGERPRINT)

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 401


async def test_refresh_wrong_fingerprint_keeps_token(
    client: AsyncClient, user: User
) -> None:
    tokens = await login(client, user.email, DEFAULT_PASSWORD, FINGERPRINT)

    wrong = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"], "fingerprint": "other-device"},
    )
    assert wrong.status_code == 401

    retry = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"], "fingerprint": FINGERPRINT},
    )

    assert retry.status_code == 200


async def test_refresh_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid", "fingerprint": FINGERPRINT},
    )

    assert response.status_code == 401


async def test_logout(client: AsyncClient, user: User) -> None:
    tokens = await login(client, user.email, DEFAULT_PASSWORD)

    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200


async def test_logout_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": "invalid"}
    )

    assert response.status_code == 404


async def test_logout_all(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post("/api/v1/auth/logout/all", headers=auth_headers)

    assert response.status_code == 200


async def test_request_verify(client: AsyncClient, unverified_user: User) -> None:
    response = await client.post(
        "/api/v1/auth/request-verify", json={"email": unverified_user.email}
    )

    assert response.status_code == 200
    assert await otp_code(EMAIL_VERIFICATION, unverified_user.id)


async def test_request_verify_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/request-verify", json={"email": "nobody@example.com"}
    )

    assert response.status_code == 404


async def test_request_verify_already_verified(client: AsyncClient, user: User) -> None:
    response = await client.post(
        "/api/v1/auth/request-verify", json={"email": user.email}
    )

    assert response.status_code == 409


async def test_verify_email(client: AsyncClient, unverified_user: User) -> None:
    await client.post(
        "/api/v1/auth/request-verify", json={"email": unverified_user.email}
    )
    code = await otp_code(EMAIL_VERIFICATION, unverified_user.id)

    response = await client.post(
        "/api/v1/auth/verify",
        json={"email": unverified_user.email, "otp_code": code},
    )

    assert response.status_code == 200
    assert response.json()["is_verified"] is True


async def test_verify_email_wrong_code(
    client: AsyncClient, unverified_user: User
) -> None:
    await client.post(
        "/api/v1/auth/request-verify", json={"email": unverified_user.email}
    )

    response = await client.post(
        "/api/v1/auth/verify",
        json={"email": unverified_user.email, "otp_code": "000000"},
    )

    assert response.status_code == 400


async def test_verify_email_without_code(
    client: AsyncClient, unverified_user: User
) -> None:
    response = await client.post(
        "/api/v1/auth/verify",
        json={"email": unverified_user.email, "otp_code": "123456"},
    )

    assert response.status_code == 404


async def test_verify_email_too_many_attempts(
    client: AsyncClient, unverified_user: User
) -> None:
    await client.post(
        "/api/v1/auth/request-verify", json={"email": unverified_user.email}
    )

    codes = []
    for _ in range(6):
        response = await client.post(
            "/api/v1/auth/verify",
            json={"email": unverified_user.email, "otp_code": "000000"},
        )
        codes.append(response.status_code)

    assert codes[-1] == 429


async def test_request_reset_password(client: AsyncClient, user: User) -> None:
    response = await client.post(
        "/api/v1/auth/request-reset-password", json={"email": user.email}
    )

    assert response.status_code == 200
    assert await otp_code(RESET_PASSWORD, user.id)


async def test_request_reset_password_unverified_user(
    client: AsyncClient, unverified_user: User
) -> None:
    response = await client.post(
        "/api/v1/auth/request-reset-password", json={"email": unverified_user.email}
    )

    assert response.status_code == 403


async def test_reset_password(
    client: AsyncClient, session: AsyncSession, user: User
) -> None:
    await client.post("/api/v1/auth/request-reset-password", json={"email": user.email})
    code = await otp_code(RESET_PASSWORD, user.id)
    new_password = "NewPassword123!"

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": user.email, "otp_code": code, "new_password": new_password},
    )

    assert response.status_code == 200
    await session.refresh(user)
    assert verify_password(new_password, user.password)


async def test_reset_password_wrong_code(client: AsyncClient, user: User) -> None:
    await client.post("/api/v1/auth/request-reset-password", json={"email": user.email})

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": user.email,
            "otp_code": "000000",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
