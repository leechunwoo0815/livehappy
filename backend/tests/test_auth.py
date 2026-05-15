import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"username": "newuser", "email": "new@test.com", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"username": "dup", "email": "dup@test.com", "password": "Test1234!"},
    )
    resp = await client.post(
        "/auth/register",
        json={"username": "dup2", "email": "dup@test.com", "password": "Test1234!"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"username": "loginuser", "email": "login@test.com", "password": "Test1234!"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "login@test.com", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"username": "badpw", "email": "badpw@test.com", "password": "Test1234!"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "badpw@test.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "refreshuser", "email": "refresh@test.com", "password": "Test1234!"},
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
