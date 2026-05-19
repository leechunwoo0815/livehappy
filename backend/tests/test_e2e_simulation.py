"""E2E simulation: Guest / Host / Admin full journey tests."""
import pytest
from app.models.listing import Listing
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _approve(db: AsyncSession, listing_id: str):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing:
        listing.status = "approved"
        await db.commit()


async def _complete_booking(db: AsyncSession, booking_id: str):
    from app.models.booking import Booking

    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if booking:
        booking.status = "completed"
        await db.commit()


# ============================================================
# GUEST JOURNEY
# ============================================================


@pytest.mark.asyncio
async def test_guest_journey(client: AsyncClient, db_session: AsyncSession):  # noqa: PLR0915
    # 1. Register guest
    reg = await client.post(
        "/api/auth/register",
        json={"username": "sim_guest", "email": "sim_guest@test.com", "password": "Test1234!"},
    )
    guest_token = reg.json()["data"]["access_token"]
    gh = {"Authorization": f"Bearer {guest_token}"}

    # 2. Search listings (public, empty)
    r = await client.get("/api/listings/search")
    assert r.status_code == 200

    # 3. Register host
    host_reg = await client.post(
        "/api/auth/register",
        json={"username": "sim_host", "email": "sim_host@test.com", "password": "Test1234!"},
    )
    host_token = host_reg.json()["data"]["access_token"]
    hh = {"Authorization": f"Bearer {host_token}"}

    # 4. Host creates listing
    r = await client.post(
        "/api/listings/",
        json={"title": "E2E测试房源", "city": "北京", "price_per_night": 200, "max_guests": 3},
        headers=hh,
    )
    assert r.status_code == 201
    lid = r.json()["data"]["id"]
    assert r.json()["data"]["status"] == "pending"

    # 5. Guest tries to book unapproved listing -> 404
    r = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 1},
        headers=gh,
    )
    assert r.status_code == 404

    # 6. Register admin + approve listing
    admin_reg = await client.post(
        "/api/auth/register",
        json={"username": "sim_admin", "email": "sim_admin@test.com", "password": "Test1234!"},
    )
    admin_token = admin_reg.json()["data"]["access_token"]
    ah = {"Authorization": f"Bearer {admin_token}"}
    # Set admin role via DB
    from app.models.user import User

    me = await client.get("/api/auth/me", headers=ah)
    admin_id = me.json()["data"]["id"]
    user = await db_session.get(User, admin_id)
    user.role = "admin"
    await db_session.commit()

    r = await client.post(f"/api/listings/{lid}/approve", json={"action": "approve"}, headers=ah)
    assert r.status_code == 200

    # 7. Search after approval
    r = await client.get("/api/listings/search", params={"city": "北京"})
    found = [x for x in r.json()["data"] if x["id"] == lid]
    assert len(found) == 1

    # 8. Guest creates booking
    r = await client.post(
        "/api/bookings/",
        json={"listing_id": lid, "check_in": "2026-07-01", "check_out": "2026-07-03", "guests": 2},
        headers=gh,
    )
    assert r.status_code == 201
    bid = r.json()["data"]["id"]
    assert r.json()["data"]["status"] == "pending"
    assert r.json()["data"]["total_price"] == 400

    # 9. Overlap booking rejected
    r = await client.post(
        "/api/bookings/",
        json={
            "listing_id": lid,
            "check_in": "2026-07-02",
            "check_out": "2026-07-04",
            "guests": 1,
        },
        headers=gh,
    )
    assert r.status_code == 409

    # 10. Guest pays
    r = await client.post(f"/api/bookings/{bid}/pay", headers=gh)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "paid"
    assert r.json()["data"]["platform_fee"] == 40
    assert r.json()["data"]["host_payout"] == 360

    # 11. Double pay rejected
    r = await client.post(f"/api/bookings/{bid}/pay", headers=gh)
    assert r.status_code == 400

    # 12. Guest tries review before completion
    r = await client.post(
        "/api/reviews/",
        params={"listing_id": lid, "booking_id": bid, "rating": 5, "content": "很好"},
        headers=gh,
    )
    assert r.status_code == 400

    # 13. Complete booking + review
    await _complete_booking(db_session, bid)
    r = await client.post(
        "/api/reviews/",
        params={"listing_id": lid, "booking_id": bid, "rating": 5, "content": "非常好的房源！"},
        headers=gh,
    )
    assert r.status_code == 200
    review_id = r.json()["data"]["id"]

    # 14. Duplicate review rejected
    r = await client.post(
        "/api/reviews/",
        params={"listing_id": lid, "booking_id": bid, "rating": 4},
        headers=gh,
    )
    assert r.status_code == 409

    # 15. Host replies to review (P0)
    r = await client.post(
        f"/api/reviews/{review_id}/reply",
        json={"reply": "感谢您的好评！"},
        headers=hh,
    )
    assert r.status_code == 200
    assert r.json()["data"]["reply"] == "感谢您的好评！"

    # 16. Guest sends message to host
    r = await client.get("/api/auth/me", headers=hh)
    host_id = r.json()["data"]["id"]
    r = await client.post(
        "/api/messages/send",
        json={"receiver_id": host_id, "content": "你好，房源还在吗？"},
        headers=gh,
    )
    assert r.status_code == 201

    # 17. Host reads conversation
    r = await client.get("/api/messages/conversations", headers=hh)
    assert r.status_code == 200
    conv_id = r.json()["data"][0]["id"]

    # 18. Host marks as read
    r = await client.post(f"/api/messages/conversations/{conv_id}/read", headers=hh)
    assert r.status_code == 200

    # P1-3: Message unread count
    r = await client.get("/api/messages/unread-count", headers=hh)
    assert r.status_code == 200
    assert r.json()["data"]["unread_count"] == 0

    # 19. Guest creates social note
    r = await client.post(
        "/api/social/notes",
        json={"title": "E2E旅行日记", "content": "今天入住了测试房源，非常满意！"},
        headers=gh,
    )
    assert r.status_code == 200
    nid = r.json()["data"]["id"]

    # 20. Host likes note
    r = await client.post(f"/api/social/notes/{nid}/like", headers=hh)
    assert r.status_code == 200

    # 21. Host double-like rejected
    r = await client.post(f"/api/social/notes/{nid}/like", headers=hh)
    assert r.status_code == 409

    # 22. Host comments on note
    r = await client.post(
        f"/api/social/notes/{nid}/comments",
        params={"content": "欢迎下次再来！"},
        headers=hh,
    )
    assert r.status_code == 200

    # 23. Host follows guest
    r = await client.get("/api/auth/me", headers=gh)
    guest_id = r.json()["data"]["id"]
    r = await client.post(f"/api/social/follow/{guest_id}", headers=hh)
    assert r.status_code == 200

    # 24. Double follow rejected
    r = await client.post(f"/api/social/follow/{guest_id}", headers=hh)
    assert r.status_code == 409

    # 25. Guest views notifications
    r = await client.get("/api/notifications/", headers=gh)
    assert r.status_code == 200
    assert "unread_count" in r.json()["data"]

    # P1-1: Guest favorites listing
    r = await client.post(f"/api/listings/{lid}/favorite", headers=gh)
    assert r.status_code == 200
    assert r.json()["data"]["favorited"] is True

    # P1-1: Favorite status
    r = await client.get(f"/api/listings/{lid}/favorite/status", headers=gh)
    assert r.status_code == 200
    assert r.json()["data"]["favorited"] is True

    # P1-1: Guest lists favorites
    r = await client.get("/api/users/favorites", headers=gh)
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 1

    # P1-2: Guest views booking detail with listing info
    r = await client.get(f"/api/bookings/{bid}", headers=gh)
    assert r.status_code == 200
    detail = r.json()["data"]
    assert detail["listing"] is not None
    assert detail["listing"]["title"] == "E2E测试房源"
    assert detail["listing"]["city"] == "北京"

    # 26. Guest logout
    r = await client.post("/api/auth/logout", headers=gh)
    assert r.status_code == 200


# ============================================================
# HOST JOURNEY
# ============================================================


@pytest.mark.asyncio
async def test_host_journey(client: AsyncClient, db_session: AsyncSession):  # noqa: PLR0915
    # Setup: register host
    host_reg = await client.post(
        "/api/auth/register",
        json={"username": "hj_host", "email": "hj_host@test.com", "password": "Test1234!"},
    )
    host_token = host_reg.json()["data"]["access_token"]
    hh = {"Authorization": f"Bearer {host_token}"}

    # 27. Host creates a new listing
    r = await client.post(
        "/api/listings/",
        json={
            "title": "房东测试房源",
            "city": "上海",
            "price_per_night": 500,
            "max_guests": 4,
            "description": "精装修大床房",
        },
        headers=hh,
    )
    assert r.status_code == 201
    lid2 = r.json()["data"]["id"]

    # 28. Host adds photo
    r = await client.post(
        f"/api/listings/{lid2}/photos?url=/uploads/test.png&is_primary=true",
        headers=hh,
    )
    assert r.status_code == 201

    # 29. Host lists photos
    r = await client.get(f"/api/listings/{lid2}/photos")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1

    # 30. Admin approves
    admin_reg = await client.post(
        "/api/auth/register",
        json={"username": "hj_admin", "email": "hj_admin@test.com", "password": "Test1234!"},
    )
    admin_token = admin_reg.json()["data"]["access_token"]
    ah = {"Authorization": f"Bearer {admin_token}"}
    from app.models.user import User

    me = await client.get("/api/auth/me", headers=ah)
    admin_id = me.json()["data"]["id"]
    user = await db_session.get(User, admin_id)
    user.role = "admin"
    await db_session.commit()

    r = await client.post(f"/api/listings/{lid2}/approve", json={"action": "approve"}, headers=ah)
    assert r.status_code == 200

    # 31. Guest books host's listing
    guest_reg = await client.post(
        "/api/auth/register",
        json={"username": "hj_guest", "email": "hj_guest@test.com", "password": "Test1234!"},
    )
    guest_token = guest_reg.json()["data"]["access_token"]
    gh = {"Authorization": f"Bearer {guest_token}"}

    r = await client.post(
        "/api/bookings/",
        json={
            "listing_id": lid2,
            "check_in": "2026-08-01",
            "check_out": "2026-08-05",
            "guests": 2,
        },
        headers=gh,
    )
    assert r.status_code == 201
    bid2 = r.json()["data"]["id"]

    # 32. Guest pays
    r = await client.post(f"/api/bookings/{bid2}/pay", headers=gh)
    assert r.status_code == 200
    assert r.json()["data"]["host_payout"] == 1800

    # 33. Host views bookings as host
    r = await client.get("/api/bookings/?role=host", headers=hh)
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1

    # 34. Host views booking detail with listing info (P1-2)
    r = await client.get(f"/api/bookings/{bid2}", headers=hh)
    assert r.status_code == 200
    detail = r.json()["data"]
    assert detail["id"] == bid2
    assert detail["listing"] is not None
    assert detail["listing"]["title"] == "房东测试房源"

    # 35. Host updates listing title
    r = await client.put(
        f"/api/listings/{lid2}",
        json={"title": "豪华大床房（已更新）"},
        headers=hh,
    )
    assert r.status_code == 200
    assert r.json()["data"]["title"] == "豪华大床房（已更新）"

    # 36. Complete booking + guest writes review
    await _complete_booking(db_session, bid2)
    r = await client.post(
        "/api/reviews/",
        params={
            "listing_id": lid2,
            "booking_id": bid2,
            "rating": 4,
            "content": "不错但可以更好",
        },
        headers=gh,
    )
    assert r.status_code == 200
    review_id = r.json()["data"]["id"]

    # 37. Host replies to review (P0 feature)
    r = await client.post(
        f"/api/reviews/{review_id}/reply",
        json={"reply": "感谢您的评价，我们会继续改进！"},
        headers=hh,
    )
    assert r.status_code == 200
    assert r.json()["data"]["reply"] == "感谢您的评价，我们会继续改进！"

    # 38. Host views listing reviews
    r = await client.get(f"/api/reviews/listing/{lid2}")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1

    # 39. Host cancels another booking
    r = await client.post(
        "/api/bookings/",
        json={
            "listing_id": lid2,
            "check_in": "2026-09-01",
            "check_out": "2026-09-03",
            "guests": 1,
        },
        headers=gh,
    )
    assert r.status_code == 201
    bid3 = r.json()["data"]["id"]
    r = await client.post(f"/api/bookings/{bid3}/cancel", json={"reason": "房东取消"}, headers=hh)
    assert r.status_code == 200

    # 40. Host deletes listing (soft delete)
    r = await client.post(
        "/api/listings/",
        json={"title": "待删除房源", "city": "测试", "price_per_night": 1, "max_guests": 1},
        headers=hh,
    )
    assert r.status_code == 201
    lid3 = r.json()["data"]["id"]
    r = await client.delete(f"/api/listings/{lid3}", headers=hh)
    assert r.status_code == 200

    # 41. Deleted listing not in search
    r = await client.get("/api/listings/search?city=测试")
    found = [x for x in r.json()["data"] if x["id"] == lid3]
    assert len(found) == 0


# ============================================================
# ADMIN JOURNEY
# ============================================================


@pytest.mark.asyncio
async def test_admin_journey(client: AsyncClient, db_session: AsyncSession):  # noqa: PLR0915
    # Setup: register admin
    admin_reg = await client.post(
        "/api/auth/register",
        json={"username": "aj_admin", "email": "aj_admin@test.com", "password": "Test1234!"},
    )
    admin_token = admin_reg.json()["data"]["access_token"]
    ah = {"Authorization": f"Bearer {admin_token}"}
    from app.models.user import User

    me = await client.get("/api/auth/me", headers=ah)
    admin_id = me.json()["data"]["id"]
    user = await db_session.get(User, admin_id)
    user.role = "admin"
    await db_session.commit()

    # Register a guest to manage
    guest_reg = await client.post(
        "/api/auth/register",
        json={"username": "aj_guest", "email": "aj_guest@test.com", "password": "Test1234!"},
    )
    guest_token = guest_reg.json()["data"]["access_token"]
    gh = {"Authorization": f"Bearer {guest_token}"}
    me = await client.get("/api/auth/me", headers=gh)
    target_user_id = me.json()["data"]["id"]

    # Create a listing to manage
    host_reg = await client.post(
        "/api/auth/register",
        json={"username": "aj_host", "email": "aj_host@test.com", "password": "Test1234!"},
    )
    host_token = host_reg.json()["data"]["access_token"]
    hh = {"Authorization": f"Bearer {host_token}"}
    r = await client.post(
        "/api/listings/",
        json={"title": "管理测试房源", "city": "管理城", "price_per_night": 100, "max_guests": 2},
        headers=hh,
    )
    target_listing_id = r.json()["data"]["id"]

    # 42. Admin views stats
    r = await client.get("/api/admin/stats", headers=ah)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["total_users"] >= 3
    assert d["total_listings"] >= 1

    # 43. Admin lists users
    r = await client.get("/api/admin/users", headers=ah)
    assert r.status_code == 200
    assert len(r.json()["data"]["items"]) >= 3

    # 44. Admin lists listings
    r = await client.get("/api/admin/listings", headers=ah)
    assert r.status_code == 200

    # 45. Admin views audit logs
    r = await client.get("/api/admin/audit-logs", headers=ah)
    assert r.status_code == 200

    # 46. Admin bans guest
    r = await client.post(f"/api/admin/users/{target_user_id}/ban", headers=ah)
    assert r.status_code == 200

    # 47. Banned guest gets 403
    r = await client.get("/api/bookings/", headers=gh)
    assert r.status_code == 403

    # 48. Admin unbans guest
    r = await client.post(f"/api/admin/users/{target_user_id}/unban", headers=ah)
    assert r.status_code == 200

    # 49. Admin changes user role
    r = await client.put(
        f"/api/admin/users/{target_user_id}/role", json={"role": "host"}, headers=ah
    )
    assert r.status_code == 200

    # 50. Admin approves listing
    r = await client.post(
        f"/api/listings/{target_listing_id}/approve",
        json={"action": "approve"},
        headers=ah,
    )
    assert r.status_code == 200

    # 51. Non-admin gets 403
    r = await client.get("/api/admin/stats", headers=gh)
    assert r.status_code == 403

    # 52. Search sorting (P1-4)
    r = await client.get("/api/listings/search?sort_by=price_asc")
    assert r.status_code == 200
    prices = [x["price_per_night"] for x in r.json()["data"]]
    assert prices == sorted(prices)

    r = await client.get("/api/listings/search?sort_by=price_desc")
    assert r.status_code == 200
    prices = [x["price_per_night"] for x in r.json()["data"]]
    assert prices == sorted(prices, reverse=True)
