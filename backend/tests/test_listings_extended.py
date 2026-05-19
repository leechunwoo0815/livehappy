import pytest
from app.models.listing import Listing
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_approve_listing_as_admin(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "host_app", "email": "host_app@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    c = await client.post(
        "/api/listings/",
        json={"title": "ApproveTest", "city": "BJ", "price_per_night": 100, "max_guests": 2},
        headers={"Authorization": f"Bearer {t1}"},
    )
    lid = c.json()["data"]["id"]

    await client.post(
        "/api/auth/register",
        json={"username": "admin_app", "email": "admin_app@test.com", "password": "Test1234!"},
    )
    admin = (
        await db_session.execute(select(User).where(User.email == "admin_app@test.com"))
    ).scalar_one()
    admin.role = "admin"
    await db_session.commit()
    t2 = (
        await client.post(
            "/api/auth/login", json={"email": "admin_app@test.com", "password": "Test1234!"}
        )
    ).json()["data"]["access_token"]

    r = await client.post(
        f"/api/listings/{lid}/approve",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "approved"


@pytest.mark.asyncio
async def test_approve_listing_as_non_admin(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "host_na", "email": "host_na@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    c = await client.post(
        "/api/listings/",
        json={"title": "NoAdmin", "city": "SH", "price_per_night": 200, "max_guests": 2},
        headers={"Authorization": f"Bearer {t1}"},
    )
    lid = c.json()["data"]["id"]
    r = await client.post(
        f"/api/listings/{lid}/approve",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_approve_listing_no_auth(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "host_noa", "email": "host_noa@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    c = await client.post(
        "/api/listings/",
        json={"title": "NoAuth", "city": "GZ", "price_per_night": 300, "max_guests": 2},
        headers={"Authorization": f"Bearer {t1}"},
    )
    lid = c.json()["data"]["id"]
    r = await client.post(f"/api/listings/{lid}/approve", json={"action": "approve"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_reject_listing(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "host_rej", "email": "host_rej@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    c = await client.post(
        "/api/listings/",
        json={"title": "RejectTest", "city": "SZ", "price_per_night": 150, "max_guests": 2},
        headers={"Authorization": f"Bearer {t1}"},
    )
    lid = c.json()["data"]["id"]
    await client.post(
        "/api/auth/register",
        json={"username": "admin_rej", "email": "admin_rej@test.com", "password": "Test1234!"},
    )
    admin = (
        await db_session.execute(select(User).where(User.email == "admin_rej@test.com"))
    ).scalar_one()
    admin.role = "admin"
    await db_session.commit()
    t2 = (
        await client.post(
            "/api/auth/login", json={"email": "admin_rej@test.com", "password": "Test1234!"}
        )
    ).json()["data"]["access_token"]
    r = await client.post(
        f"/api/listings/{lid}/approve",
        json={"action": "reject"},
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "rejected"


@pytest.mark.asyncio
async def test_add_photo(client: AsyncClient):
    r = await client.post(
        "/api/auth/register",
        json={"username": "photohost", "email": "photohost@test.com", "password": "Test1234!"},
    )
    t = r.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {t}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "PhotoL", "city": "CD", "price_per_night": 100, "max_guests": 2},
        headers=h,
    )
    lid = c.json()["data"]["id"]
    r = await client.post(
        f"/api/listings/{lid}/photos?url=https://example.com/p.jpg&is_primary=true", headers=h
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_list_photos(client: AsyncClient):
    r = await client.post(
        "/api/auth/register",
        json={"username": "photolist", "email": "photolist@test.com", "password": "Test1234!"},
    )
    t = r.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {t}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "PhotoListL", "city": "NJ", "price_per_night": 120, "max_guests": 2},
        headers=h,
    )
    lid = c.json()["data"]["id"]
    await client.post(f"/api/listings/{lid}/photos?url=https://example.com/p1.jpg", headers=h)
    r = await client.get(f"/api/listings/{lid}/photos")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_create_listing_unauthorized(client: AsyncClient):
    r = await client.post(
        "/api/listings/",
        json={"title": "Bad", "city": "XX", "price_per_night": 100, "max_guests": 2},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_update_listing_other_host(client: AsyncClient):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "host_up1", "email": "host_up1@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "OtherHost", "city": "XA", "price_per_night": 100, "max_guests": 2},
        headers=h1,
    )
    lid = c.json()["data"]["id"]
    r2 = await client.post(
        "/api/auth/register",
        json={"username": "host_up2", "email": "host_up2@test.com", "password": "Test1234!"},
    )
    t2 = r2.json()["data"]["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}
    r = await client.put(f"/api/listings/{lid}", json={"title": "Hacked"}, headers=h2)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_search_approved_listings(client: AsyncClient, db_session: AsyncSession):
    r = await client.post(
        "/api/auth/register",
        json={"username": "searchapp", "email": "searchapp@test.com", "password": "Test1234!"},
    )
    t = r.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {t}"}
    c = await client.post(
        "/api/listings/",
        json={"title": "Searchable", "city": "HZ", "price_per_night": 500, "max_guests": 4},
        headers=h,
    )
    lid = c.json()["data"]["id"]
    listing = await db_session.get(Listing, lid)
    listing.status = "approved"
    await db_session.commit()
    r = await client.get("/api/listings/search?city=HZ")
    assert r.status_code == 200
    assert any(item["id"] == lid for item in r.json()["data"])
