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


@pytest.mark.asyncio
async def test_host_reply_to_review(client: AsyncClient, db_session: AsyncSession):
    # Host registers and creates listing
    r_host = await client.post(
        "/api/auth/register",
        json={"username": "replyhost", "email": "replyhost@test.com", "password": "Test1234!"},
    )
    ht = r_host.json()["data"]["access_token"]
    hh = {"Authorization": f"Bearer {ht}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "ReplyL", "city": "BJ", "price_per_night": 100, "max_guests": 2},
        headers=hh,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()

    # Guest books, pays, completes, reviews
    r_guest = await client.post(
        "/api/auth/register",
        json={"username": "replyguest", "email": "replyguest@test.com", "password": "Test1234!"},
    )
    gt = r_guest.json()["data"]["access_token"]
    gh = {"Authorization": f"Bearer {gt}"}
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-01", "check_out": "2026-12-03", "guests": 1},
        headers=gh,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    r = await client.post(
        f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=4&content=不错", headers=gh
    )
    assert r.status_code == 200
    rid = r.json()["data"]["id"]

    # Host replies
    r = await client.post(
        f"/api/reviews/{rid}/reply",
        json={"reply": "感谢评价！"},
        headers=hh,
    )
    assert r.status_code == 200
    assert r.json()["data"]["reply"] == "感谢评价！"


@pytest.mark.asyncio
async def test_host_reply_duplicate(client: AsyncClient, db_session: AsyncSession):
    r_host = await client.post(
        "/api/auth/register",
        json={"username": "replyhost2", "email": "replyhost2@test.com", "password": "Test1234!"},
    )
    ht = r_host.json()["data"]["access_token"]
    hh = {"Authorization": f"Bearer {ht}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "ReplyL2", "city": "SH", "price_per_night": 100, "max_guests": 2},
        headers=hh,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()

    r_guest = await client.post(
        "/api/auth/register",
        json={"username": "replyguest2", "email": "replyguest2@test.com", "password": "Test1234!"},
    )
    gt = r_guest.json()["data"]["access_token"]
    gh = {"Authorization": f"Bearer {gt}"}
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-05", "check_out": "2026-12-07", "guests": 1},
        headers=gh,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    r = await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=5", headers=gh)
    rid = r.json()["data"]["id"]

    # First reply succeeds
    await client.post(f"/api/reviews/{rid}/reply", json={"reply": "谢谢"}, headers=hh)
    # Second reply fails
    r = await client.post(f"/api/reviews/{rid}/reply", json={"reply": "再次感谢"}, headers=hh)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_non_host_reply_forbidden(client: AsyncClient, db_session: AsyncSession):
    r_host = await client.post(
        "/api/auth/register",
        json={"username": "replyhost3", "email": "replyhost3@test.com", "password": "Test1234!"},
    )
    ht = r_host.json()["data"]["access_token"]
    hh = {"Authorization": f"Bearer {ht}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "ReplyL3", "city": "GZ", "price_per_night": 100, "max_guests": 2},
        headers=hh,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()

    r_guest = await client.post(
        "/api/auth/register",
        json={"username": "replyguest3", "email": "replyguest3@test.com", "password": "Test1234!"},
    )
    gt = r_guest.json()["data"]["access_token"]
    gh = {"Authorization": f"Bearer {gt}"}
    b = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-12-10", "check_out": "2026-12-12", "guests": 1},
        headers=gh,
    )
    bid = b.json()["data"]["id"]
    booking = await db_session.get(Booking, bid)
    booking.status = "completed"
    await db_session.commit()
    r = await client.post(f"/api/reviews/?listing_id={lid}&booking_id={bid}&rating=3", headers=gh)
    rid = r.json()["data"]["id"]

    # Guest tries to reply to their own review (not host)
    r = await client.post(f"/api/reviews/{rid}/reply", json={"reply": "自己回复自己"}, headers=gh)
    assert r.status_code == 403
