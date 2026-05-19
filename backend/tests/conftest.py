import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

from app.database import get_db
from app.main import app
from app.models import Base


class _MockRedisClient:
    def __init__(self):
        self._store: dict[str, str] = {}
        self._set_store: dict[str, set[str]] = {}

    def reset(self):
        self._store.clear()
        self._set_store.clear()

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value
        _ = ex

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self._store.pop(k, None)

    async def incr(self, key: str) -> int:
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        _ = seconds
        return key in self._store

    async def sadd(self, key: str, member: str) -> None:
        self._set_store.setdefault(key, set()).add(member)

    async def srem(self, key: str, member: str) -> None:
        self._set_store.get(key, set()).discard(member)

    async def sismember(self, key: str, member: str) -> bool:
        return member in self._set_store.get(key, set())

    async def ping(self) -> bool:
        return True


mock_redis_instance = _MockRedisClient()


def _get_mock_redis():
    return mock_redis_instance


@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    import app.redis as ar

    ar.get_redis = _get_mock_redis
    import app.services.auth as sa

    sa.get_redis = _get_mock_redis
    import app.middleware.auth as ma

    ma.get_redis = _get_mock_redis
    import app.routers.auth as ra

    ra.get_redis = _get_mock_redis
    import app.routers.health as rh

    rh.get_redis = _get_mock_redis
    import app.services.admin as sadm

    sadm.get_redis = _get_mock_redis
    yield


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    mock_redis_instance.reset()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session


async def _register_user(
    client: AsyncClient, username: str, email: str, password: str = "Test1234!"
) -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    return resp.json()["data"]


async def _make_admin_user(client: AsyncClient, db: AsyncSession, prefix: str = "adm"):
    data = await _register_user(client, f"{prefix}admin", f"{prefix}admin@test.com")
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Set role to admin via direct DB update
    from app.config import settings
    from jose import jwt as jose_jwt

    payload = jose_jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id = payload["sub"]
    from app.models.user import User

    user = await db.get(User, user_id)
    user.role = "admin"
    await db.commit()
    return token, headers, user_id


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, db_session: AsyncSession):
    token, _, _ = await _make_admin_user(client, db_session, "fx")
    return token


@pytest_asyncio.fixture
async def admin_headers(admin_token: str):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def user_token(client: AsyncClient):
    data = await _register_user(client, "fxuser", "fxuser@test.com")
    return data["access_token"]


@pytest_asyncio.fixture
async def user_headers(user_token: str):
    return {"Authorization": f"Bearer {user_token}"}
