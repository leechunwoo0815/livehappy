import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_chat(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "aichat", "email": "aichat@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    resp = await client.post(
        "/api/ai/chat", json={"content": "Hello"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "reply" in resp.json()["data"]
    assert resp.json()["data"]["role"] == "assistant"


@pytest.mark.asyncio
async def test_ai_chat_no_auth(client: AsyncClient):
    resp = await client.post("/api/ai/chat", json={"content": "Hello"})
    assert resp.status_code == 401
