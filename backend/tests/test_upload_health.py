import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_image(client: AsyncClient, user_headers: dict):
    # Create a minimal PNG file
    png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    r = await client.post(
        "/api/upload",
        files={"file": ("test.png", io.BytesIO(png_data), "image/png")},
        headers=user_headers,
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["url"].startswith("/uploads/")
    assert data["url"].endswith(".png")


@pytest.mark.asyncio
async def test_upload_invalid_extension(client: AsyncClient, user_headers: dict):
    r = await client.post(
        "/api/upload",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=user_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_upload_unauthorized(client: AsyncClient):
    png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
    r = await client.post(
        "/api/upload",
        files={"file": ("test.png", io.BytesIO(png_data), "image/png")},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "database" in data["data"]["services"]
    assert "redis" in data["data"]["services"]
