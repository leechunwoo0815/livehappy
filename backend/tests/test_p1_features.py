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
async def test_toggle_favorite(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "fav_user", "email": "fav@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "收藏房源", "city": "杭州", "price_per_night": 300, "max_guests": 2},
        headers=headers,
    )
    lid = create.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    # Toggle on
    resp = await client.post(f"/api/listings/{lid}/favorite", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["favorited"] is True
    # Toggle off
    resp = await client.post(f"/api/listings/{lid}/favorite", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["favorited"] is False


@pytest.mark.asyncio
async def test_favorite_status(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "fav2", "email": "fav2@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "测试状态", "city": "深圳", "price_per_night": 200, "max_guests": 2},
        headers=headers,
    )
    lid = create.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    # Check status (not favorited)
    resp = await client.get(f"/api/listings/{lid}/favorite/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["favorited"] is False
    # Toggle on
    await client.post(f"/api/listings/{lid}/favorite", headers=headers)
    resp = await client.get(f"/api/listings/{lid}/favorite/status", headers=headers)
    assert resp.json()["data"]["favorited"] is True


@pytest.mark.asyncio
async def test_list_favorites(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "fav3", "email": "fav3@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "收藏列表", "city": "广州", "price_per_night": 180, "max_guests": 3},
        headers=headers,
    )
    lid = create.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    await client.post(f"/api/listings/{lid}/favorite", headers=headers)
    resp = await client.get("/api/users/favorites", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1
    assert any(f["listing_id"] == lid for f in data["items"])


@pytest.mark.asyncio
async def test_unfavorite_nonexistent_listing(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "fav4", "email": "fav4@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/listings/nonexistent/favorite", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_sort_by_price(client: AsyncClient, db_session: AsyncSession):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "sort_host", "email": "sort@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for price in [500, 100, 300]:
        r = await client.post(
            "/api/listings/",
            json={
                "title": f"排序{price}",
                "city": "排序城",
                "price_per_night": price,
                "max_guests": 2,
            },
            headers=headers,
        )
        lid = r.json()["data"]["id"]
        await _approve_listing(db_session, lid)

    resp = await client.get("/api/listings/search?city=排序城&sort_by=price_asc")
    assert resp.status_code == 200
    prices = [item["price_per_night"] for item in resp.json()["data"]]
    assert prices == sorted(prices)

    resp = await client.get("/api/listings/search?city=排序城&sort_by=price_desc")
    assert resp.status_code == 200
    prices = [item["price_per_night"] for item in resp.json()["data"]]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.asyncio
async def test_booking_detail_includes_listing(client: AsyncClient, db_session: AsyncSession):
    guest_reg = await client.post(
        "/api/auth/register",
        json={"username": "bd_guest", "email": "bd_guest@test.com", "password": "Test1234!"},
    )
    guest_token = guest_reg.json()["data"]["access_token"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}
    host_reg = await client.post(
        "/api/auth/register",
        json={"username": "bd_host", "email": "bd_host@test.com", "password": "Test1234!"},
    )
    host_token = host_reg.json()["data"]["access_token"]
    host_headers = {"Authorization": f"Bearer {host_token}"}
    create = await client.post(
        "/api/listings/",
        json={"title": "订单详情房源", "city": "成都", "price_per_night": 200, "max_guests": 2},
        headers=host_headers,
    )
    lid = create.json()["data"]["id"]
    await _approve_listing(db_session, lid)
    book = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-08-01", "check_out": "2026-08-03", "guests": 1},
        headers=guest_headers,
    )
    assert book.status_code == 201
    bid = book.json()["data"]["id"]
    resp = await client.get(f"/api/bookings/{bid}", headers=guest_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "listing" in data
    assert data["listing"]["title"] == "订单详情房源"
    assert data["listing"]["city"] == "成都"


@pytest.mark.asyncio
async def test_message_unread_count(client: AsyncClient):
    reg1 = await client.post(
        "/api/auth/register",
        json={"username": "uc1", "email": "uc1@test.com", "password": "Test1234!"},
    )
    token1 = reg1.json()["data"]["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    reg2 = await client.post(
        "/api/auth/register",
        json={"username": "uc2", "email": "uc2@test.com", "password": "Test1234!"},
    )
    token2 = reg2.json()["data"]["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    # Get user2 id via /me
    me = await client.get("/api/auth/me", headers=headers2)
    user2_id = me.json()["data"]["id"]
    # Send messages from user1 to user2
    for i in range(3):
        await client.post(
            "/api/messages/send",
            json={"receiver_id": user2_id, "content": f"消息{i}"},
            headers=headers1,
        )
    # Check unread count for user2
    resp = await client.get("/api/messages/unread-count", headers=headers2)
    assert resp.status_code == 200
    assert resp.json()["data"]["unread_count"] == 3
    # Mark read, count should be 0
    convs = await client.get("/api/messages/conversations", headers=headers2)
    conv_id = convs.json()["data"][0]["id"]
    await client.post(f"/api/messages/conversations/{conv_id}/read", headers=headers2)
    resp = await client.get("/api/messages/unread-count", headers=headers2)
    assert resp.json()["data"]["unread_count"] == 0
