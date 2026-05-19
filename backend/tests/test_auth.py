import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/api/auth/register",
        json={"username": "newuser", "email": "new@test.com", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "dup", "email": "dup@test.com", "password": "Test1234!"},
    )
    resp = await client.post(
        "/api/auth/register",
        json={"username": "dup2", "email": "dup@test.com", "password": "Test1234!"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "loginuser", "email": "login@test.com", "password": "Test1234!"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "login@test.com", "password": "Test1234!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "badpw", "email": "badpw@test.com", "password": "Test1234!"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "badpw@test.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "refreshuser", "email": "refresh@test.com", "password": "Test1234!"},
    )
    refresh_token = reg.json()["data"]["refresh_token"]
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "logoutuser", "email": "logout@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "forgotuser", "email": "forgot@test.com", "password": "Test1234!"},
    )
    resp = await client.post("/api/auth/forgot-password", json={"email": "forgot@test.com"})
    assert resp.status_code == 200
    assert "reset_token" in resp.json()["data"]


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(client: AsyncClient):
    resp = await client.post("/api/auth/forgot-password", json={"email": "unknown@test.com"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"username": "resetuser", "email": "reset@test.com", "password": "Test1234!"},
    )
    forgot = await client.post("/api/auth/forgot-password", json={"email": "reset@test.com"})
    reset_token = forgot.json()["data"]["reset_token"]
    resp = await client.post(
        "/api/auth/reset-password",
        json={"token": reset_token, "new_password": "NewPass123!"},
    )
    assert resp.status_code == 200
    # Login with new password
    login = await client.post(
        "/api/auth/login",
        json={"email": "reset@test.com", "password": "NewPass123!"},
    )
    assert login.status_code == 200
