import pytest
from app.models.listing import Listing
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _approve_listing(db: AsyncSession, listing_id: str):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing:
        listing.status = "approved"
        await db.commit()


@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest1", "email": "guest1@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源A", "city": "北京", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    resp = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 1},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "pending"
    assert resp.json()["data"]["total_price"] == 200


@pytest.mark.asyncio
async def test_pay_booking(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest2", "email": "guest2@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源B", "city": "上海", "price_per_night": 150, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    book = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-08-01", "check_out": "2026-08-05", "guests": 2},
        headers=headers,
    )
    bid = book.json()["data"]["id"]
    resp = await client.post(f"/api/bookings/{bid}/pay", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["status"] == "paid"
    assert data["data"]["amount"] == 600
    assert data["data"]["platform_fee"] == 60
    assert data["data"]["host_payout"] == 540


@pytest.mark.asyncio
async def test_cancel_booking(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest3", "email": "guest3@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源C", "city": "广州", "price_per_night": 200, "max_guests": 3},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    book = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-09-01", "check_out": "2026-09-02", "guests": 1},
        headers=headers,
    )
    bid = book.json()["data"]["id"]
    resp = await client.post(
        f"/api/bookings/{bid}/cancel", json={"reason": "计划有变"}, headers=headers
    )
    assert resp.status_code == 200
    resp2 = await client.post(f"/api/bookings/{bid}/cancel", headers=headers)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_list_bookings(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest4", "email": "guest4@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源D", "city": "深圳", "price_per_night": 300, "max_guests": 4},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-10-01", "check_out": "2026-10-03", "guests": 2},
        headers=headers,
    )
    resp = await client.get("/api/bookings/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
