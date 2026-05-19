import pytest
from app.models.booking import Booking
from app.models.listing import Listing
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_review(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "rguest", "email": "rguest@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "RevL", "city": "BJ", "price_per_night": 100, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-01", "check_out": "2026-12-03", "guests": 1},
        headers=h1,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    r = await client.post(
        f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=5&content=Great", headers=h1
    )
    assert r.status_code == 200
    assert r.json()["data"]["rating"] == 5


@pytest.mark.asyncio
async def test_create_review_invalid_rating(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "rguest2", "email": "rguest2@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "RevL2", "city": "SH", "price_per_night": 150, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-05", "check_out": "2026-12-07", "guests": 1},
        headers=h1,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    r = await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=99", headers=h1)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_review_duplicate(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "rguest3", "email": "rguest3@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "RevL3", "city": "GZ", "price_per_night": 200, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-10", "check_out": "2026-12-12", "guests": 1},
        headers=h1,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=4", headers=h1)
    r = await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=4", headers=h1)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_reviews(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "rguest4", "email": "rguest4@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "RevL4", "city": "SZ", "price_per_night": 250, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-15", "check_out": "2026-12-17", "guests": 1},
        headers=h1,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=5", headers=h1)
    r = await client.get(f"/api/reviews/listing/{lid}")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_create_review_booking_not_completed(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "rguest5", "email": "rguest5@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "RevL5", "city": "CD", "price_per_night": 100, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-20", "check_out": "2026-12-22", "guests": 1},
        headers=h1,
    )
    bid = b.json()["data"]["id"]
    # Booking is still "pending" — should fail
    r = await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=5", headers=h1)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_review_unauthorized_booking(client: AsyncClient, db_session: AsyncSession):
    # User A creates listing and booking
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "rguest6a", "email": "rguest6a@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "RevL6", "city": "WH", "price_per_night": 100, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-25", "check_out": "2026-12-27", "guests": 1},
        headers=h1,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    # User B tries to review User A's booking
    r2 = await client.post(
        "/api/auth/register",
        json={"username": "rguest6b", "email": "rguest6b@test.com", "password": "Test1234!"},
    )
    t2 = r2.json()["data"]["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}
    r = await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=5", headers=h2)
    assert r.status_code == 403
