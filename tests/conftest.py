import os

os.environ.pop("RUNNING_IN_DOCKER", None)
os.environ["APP_CONFIG__DB__URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5433/healthdiary_test",
)
os.environ["APP_CONFIG__REDIS__URL"] = os.environ.get(
    "TEST_REDIS_URL",
    "redis://localhost:6379/15",
)
os.environ.setdefault("APP_CONFIG__SECRET_KEY", "test-secret-key")

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.limiter import limiter
from app.core.models import Base, User, db_helper
from app.core.redis_client import redis_client
from app.main import main_app
from tests.factories.user import DEFAULT_PASSWORD, create_user


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(url=str(settings.db.url), poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_redis() -> AsyncGenerator[None]:
    await redis_client.flushdb()
    limiter.reset()

    yield

    await redis_client.flushdb()
    await redis_client.connection_pool.disconnect()
    limiter.reset()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with engine.connect() as conn:
        transaction = await conn.begin()
        factory = async_sessionmaker(bind=conn, expire_on_commit=False)

        async with factory() as s:
            yield s

        await transaction.rollback()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def _override() -> AsyncGenerator[AsyncSession]:
        yield session

    main_app.dependency_overrides[db_helper.session_getter] = _override
    async with AsyncClient(
        transport=ASGITransport(app=main_app), base_url="http://test"
    ) as ac:
        yield ac

    main_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    return await create_user(session=session)


@pytest_asyncio.fixture
async def auth_headers(
    client: AsyncClient, session: AsyncSession, user: User
) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json().get('access_token')}"}
