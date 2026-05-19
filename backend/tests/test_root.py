import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_info(client: AsyncClient):
    resp = await client.get("/api/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "LiveHappy"
    assert "version" in data
