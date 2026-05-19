import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "meuser", "email": "meuser@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["username"] == "meuser"
    assert data["data"]["email"] == "meuser@test.com"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get("/api/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_refresh_token_rejected(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "refrej", "email": "refrej@test.com", "password": "Test1234!"},
    )
    refresh = reg.json()["data"]["refresh_token"]
    resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {refresh}"})
    assert resp.status_code == 401
