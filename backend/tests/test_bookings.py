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


@pytest.mark.asyncio
async def test_create_booking_overlap_dates(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest5", "email": "guest5@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源E", "city": "成都", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    # First booking
    resp1 = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-11-01", "check_out": "2026-11-05", "guests": 1},
        headers=headers,
    )
    assert resp1.status_code == 201
    # Overlapping booking on same listing
    resp2 = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-11-03", "check_out": "2026-11-07", "guests": 1},
        headers=headers,
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_create_booking_exceed_max_guests(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest6", "email": "guest6@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源F", "city": "杭州", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    resp = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-01", "check_out": "2026-12-03", "guests": 5},
        headers=headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_past_date(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest7", "email": "guest7@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源G", "city": "武汉", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    resp = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2020-01-01", "check_out": "2020-01-03", "guests": 1},
        headers=headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_booking_invalid_dates(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest8", "email": "guest8@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源H", "city": "南京", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    # check_in >= check_out
    resp = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-05", "check_out": "2026-12-01", "guests": 1},
        headers=headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_pay_booking_already_paid(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "guest9", "email": "guest9@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源I", "city": "重庆", "price_per_night": 100, "max_guests": 2},
        headers=headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    book = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-10", "check_out": "2026-12-12", "guests": 1},
        headers=headers,
    )
    bid = book.json()["data"]["id"]
    # First payment succeeds
    resp1 = await client.post(f"/api/bookings/{bid}/pay", headers=headers)
    assert resp1.status_code == 200
    # Second payment fails
    resp2 = await client.post(f"/api/bookings/{bid}/pay", headers=headers)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_list_bookings_as_host(client: AsyncClient, db_session: AsyncSession):
    # Register guest and host
    reg = await client.post(
        "/api/auth/register",
        json={"username": "host1", "email": "host1@test.com", "password": "Test1234!"},
    )
    host_token = reg.json()["data"]["access_token"]
    host_headers = {"Authorization": f"Bearer {host_token}"}

    reg2 = await client.post(
        "/api/auth/register",
        json={"username": "guest10", "email": "guest10@test.com", "password": "Test1234!"},
    )
    guest_token = reg2.json()["data"]["access_token"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}

    # Host creates listing
    listing = await client.post(
        "/api/listings/",
        json={"title": "房源J", "city": "西安", "price_per_night": 100, "max_guests": 2},
        headers=host_headers,
    )
    lid = listing.json()["data"]["id"]
    await _approve_listing(db_session, lid)

    # Guest books it
    await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-20", "check_out": "2026-12-22", "guests": 1},
        headers=guest_headers,
    )

    # Host sees it in role=host
    resp = await client.get("/api/bookings/?role=host", headers=host_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
