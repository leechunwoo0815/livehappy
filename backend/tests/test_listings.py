import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_listing(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "host1", "email": "host1@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/listings/",
        json={
            "title": "海景大床房",
            "city": "三亚",
            "price_per_night": 299,
            "max_guests": 2,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["data"]["title"] == "海景大床房"
    assert data["data"]["city"] == "三亚"


@pytest.mark.asyncio
async def test_search_listings(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "host2", "email": "host2@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/api/listings/",
        json={"title": "市区公寓", "city": "北京", "price_per_night": 199, "max_guests": 4},
        headers=headers,
    )
    # search (status is pending, not approved, so will not show)
    resp = await client.get("/api/listings/search?city=北京")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 0


@pytest.mark.asyncio
async def test_get_listing_detail(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "host3", "email": "host3@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "山间小屋", "city": "大理", "price_per_night": 399, "max_guests": 3},
        headers=headers,
    )
    listing_id = create.json()["data"]["id"]
    resp = await client.get(f"/api/listings/{listing_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "山间小屋"
    # New detail should include reviews and avg_rating
    data = resp.json()["data"]
    assert "reviews" in data
    assert "avg_rating" in data
    assert "review_count" in data


@pytest.mark.asyncio
async def test_update_listing(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "host4", "email": "host4@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "旧标题", "city": "成都", "price_per_night": 150, "max_guests": 2},
        headers=headers,
    )
    lid = create.json()["data"]["id"]
    resp = await client.put(
        f"/api/listings/{lid}",
        json={"title": "新标题"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "新标题"


@pytest.mark.asyncio
async def test_delete_listing(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "host5", "email": "host5@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "待删除", "city": "厦门", "price_per_night": 250, "max_guests": 2},
        headers=headers,
    )
    lid = create.json()["data"]["id"]
    resp = await client.delete(f"/api/listings/{lid}", headers=headers)
    assert resp.status_code == 200
    resp = await client.get(f"/api/listings/{lid}")
    assert resp.status_code == 404
