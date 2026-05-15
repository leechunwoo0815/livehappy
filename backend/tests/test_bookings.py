import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "guest1", "email": "guest1@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/listings/",
        json={"title": "房源A", "city": "北京", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["id"]
    await client.post(f"/listings/{lid}/approve", json={"action": "approve"})
    resp = await client.post(
        "/bookings/",
        json={"listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 1},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
    assert resp.json()["total_price"] == 200


@pytest.mark.asyncio
async def test_pay_booking(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "guest2", "email": "guest2@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/listings/",
        json={"title": "房源B", "city": "上海", "price_per_night": 150, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["id"]
    await client.post(f"/listings/{lid}/approve", json={"action": "approve"})
    book = await client.post(
        "/bookings/",
        json={"listing_id": lid, "check_in": "2026-08-01", "check_out": "2026-08-05", "guests": 2},
        headers=headers,
    )
    bid = book.json()["id"]
    resp = await client.post(f"/bookings/{bid}/pay", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "paid"
    assert data["amount"] == 600
    assert data["platform_fee"] == 60
    assert data["host_payout"] == 540


@pytest.mark.asyncio
async def test_cancel_booking(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "guest3", "email": "guest3@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/listings/",
        json={"title": "房源C", "city": "广州", "price_per_night": 200, "max_guests": 3},
        headers=headers,
    )
    lid = listing.json()["id"]
    await client.post(f"/listings/{lid}/approve", json={"action": "approve"})
    book = await client.post(
        "/bookings/",
        json={"listing_id": lid, "check_in": "2026-09-01", "check_out": "2026-09-02", "guests": 1},
        headers=headers,
    )
    bid = book.json()["id"]
    resp = await client.post(
        f"/bookings/{bid}/cancel", json={"reason": "计划有变"}, headers=headers
    )
    assert resp.status_code == 200
    resp2 = await client.post(f"/bookings/{bid}/cancel", headers=headers)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_list_bookings(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"username": "guest4", "email": "guest4@test.com", "password": "Test1234!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/listings/",
        json={"title": "房源D", "city": "深圳", "price_per_night": 300, "max_guests": 4},
        headers=headers,
    )
    lid = listing.json()["id"]
    await client.post(f"/listings/{lid}/approve", json={"action": "approve"})
    await client.post(
        "/bookings/",
        json={"listing_id": lid, "check_in": "2026-10-01", "check_out": "2026-10-03", "guests": 2},
        headers=headers,
    )
    resp = await client.get("/bookings/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
