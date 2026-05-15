import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_listing(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "host1", "email": "host1@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/listings/",
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
    assert data["title"] == "海景大床房"
    assert data["city"] == "三亚"


@pytest.mark.asyncio
async def test_search_listings(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "host2", "email": "host2@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/listings/",
        json={"title": "市区公寓", "city": "北京", "price_per_night": 199, "max_guests": 4},
        headers=headers,
    )
    # search (status is pending, not approved, so will not show)
    resp = await client.get("/listings/search?city=北京")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_get_listing_detail(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "host3", "email": "host3@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/listings/",
        json={"title": "山间小屋", "city": "大理", "price_per_night": 399, "max_guests": 3},
        headers=headers,
    )
    listing_id = create.json()["id"]
    resp = await client.get(f"/listings/{listing_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "山间小屋"


@pytest.mark.asyncio
async def test_update_listing(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "host4", "email": "host4@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/listings/",
        json={"title": "旧标题", "city": "成都", "price_per_night": 150, "max_guests": 2},
        headers=headers,
    )
    lid = create.json()["id"]
    resp = await client.put(
        f"/listings/{lid}",
        json={"title": "新标题"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新标题"


@pytest.mark.asyncio
async def test_delete_listing(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "host5", "email": "host5@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/listings/",
        json={"title": "待删除", "city": "厦门", "price_per_night": 250, "max_guests": 2},
        headers=headers,
    )
    lid = create.json()["id"]
    resp = await client.delete(f"/listings/{lid}", headers=headers)
    assert resp.status_code == 204
    resp = await client.get(f"/listings/{lid}")
    assert resp.status_code == 404
