import pytest
from app.models.listing import Listing
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def _make_admin(db_session: AsyncSession, client: AsyncClient, suffix: str) -> str:
    r = await client.post(
        "/api/auth/register",
        json={
            "username": f"admin_{suffix}",
            "email": f"admin_{suffix}@test.com",
            "password": "Test1234!",
        },
    )
    t = r.json()["data"]["access_token"]
    user_data = (
        await client.get("/api/users/me", headers={"Authorization": f"Bearer {t}"})
    ).json()["data"]
    uid = user_data["id"]
    admin = await db_session.get(User, uid)
    admin.role = "admin"
    await db_session.commit()
    t2 = (
        await client.post(
            "/api/auth/login", json={"email": f"admin_{suffix}@test.com", "password": "Test1234!"}
        )
    ).json()["data"]["access_token"]
    return t2


@pytest.mark.asyncio
async def _make_host(db_session: AsyncSession, client: AsyncClient, suffix: str) -> tuple[str, str]:
    r = await client.post(
        "/api/auth/register",
        json={
            "username": f"host_{suffix}",
            "email": f"host_{suffix}@test.com",
            "password": "Test1234!",
        },
    )
    t = r.json()["data"]["access_token"]
    user_data = (
        await client.get("/api/users/me", headers={"Authorization": f"Bearer {t}"})
    ).json()["data"]
    uid = user_data["id"]
    user = await db_session.get(User, uid)
    user.role = "host"
    await db_session.commit()
    return t, uid


@pytest.mark.asyncio
async def _make_user(db_session: AsyncSession, client: AsyncClient, suffix: str) -> tuple[str, str]:
    r = await client.post(
        "/api/auth/register",
        json={
            "username": f"user_{suffix}",
            "email": f"user_{suffix}@test.com",
            "password": "Test1234!",
        },
    )
    t = r.json()["data"]["access_token"]
    user_data = (
        await client.get("/api/users/me", headers={"Authorization": f"Bearer {t}"})
    ).json()["data"]
    uid = user_data["id"]
    return t, uid


@pytest.mark.asyncio
async def test_admin_stats(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "stats")
    r = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert "total_users" in d
    assert "total_listings" in d
    assert "pending_listings" in d


@pytest.mark.asyncio
async def test_admin_stats_unauthorized(client: AsyncClient):
    r = await client.get("/api/admin/stats")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_listings(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "listall")
    r = await client.get("/api/admin/listings", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert "items" in r.json()["data"]


@pytest.mark.asyncio
async def test_admin_listings_filter(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "lfilter")
    r = await client.get(
        "/api/admin/listings?status=pending", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_admin_pending_listings(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "pend")
    host_t, _ = await _make_host(db_session, client, "pend")
    c = await client.post(
        "/api/listings/",
        json={"title": "PendingT", "city": "BJ", "price_per_night": 100, "max_guests": 2},
        headers={"Authorization": f"Bearer {host_t}"},
    )
    lid = c.json()["data"]["id"]
    r = await client.get("/api/admin/listings/pending", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()["data"]["items"]]
    assert lid in ids


@pytest.mark.asyncio
async def test_admin_offline_listing(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "off")
    host_t, _ = await _make_host(db_session, client, "off")
    c = await client.post(
        "/api/listings/",
        json={"title": "OfflineT", "city": "BJ", "price_per_night": 100, "max_guests": 2},
        headers={"Authorization": f"Bearer {host_t}"},
    )
    lid = c.json()["data"]["id"]
    r = await client.post(
        f"/api/admin/listings/{lid}/offline", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 200
    listing = await db_session.get(Listing, lid)
    assert listing.is_active is False


@pytest.mark.asyncio
async def test_admin_offline_listing_not_found(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "offnf")
    r = await client.post(
        "/api/admin/listings/nonexistent/offline", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_ban_user(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "ban")
    _, uid = await _make_user(db_session, client, "ban")
    r = await client.post(f"/api/admin/users/{uid}/ban", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    user = await db_session.get(User, uid)
    assert user.is_banned is True


@pytest.mark.asyncio
async def test_admin_ban_admin(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "banadm")
    me = (await client.get("/api/users/me", headers={"Authorization": f"Bearer {t}"})).json()[
        "data"
    ]
    r = await client.post(
        f"/api/admin/users/{me['id']}/ban", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_ban_user_not_found(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "bannf")
    r = await client.post(
        "/api/admin/users/nonexistent/ban", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_admin_unban_user(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "unban")
    _, uid = await _make_user(db_session, client, "unban")
    user = await db_session.get(User, uid)
    user.is_banned = True
    await db_session.commit()
    r = await client.post(f"/api/admin/users/{uid}/unban", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    await db_session.refresh(user)
    assert user.is_banned is False


@pytest.mark.asyncio
async def test_admin_audit_logs(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "audit")
    _, uid = await _make_user(db_session, client, "audit")
    await client.post(f"/api/admin/users/{uid}/ban", headers={"Authorization": f"Bearer {t}"})
    r = await client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    logs = r.json()["data"]["items"]
    assert len(logs) >= 1
    assert logs[0]["action"] == "ban_user"


@pytest.mark.asyncio
async def test_admin_audit_logs_filter(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "auditf")
    _, uid = await _make_user(db_session, client, "auditf")
    await client.post(f"/api/admin/users/{uid}/ban", headers={"Authorization": f"Bearer {t}"})
    r = await client.get(
        "/api/admin/audit-logs?action=ban_user", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 200
    logs = r.json()["data"]["items"]
    assert all(item["action"] == "ban_user" for item in logs)


@pytest.mark.asyncio
async def test_admin_bookings(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "bk")
    r = await client.get("/api/admin/bookings", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert "items" in r.json()["data"]


@pytest.mark.asyncio
async def test_admin_bookings_filter(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "bkf")
    r = await client.get(
        "/api/admin/bookings?status=pending", headers={"Authorization": f"Bearer {t}"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_admin_users(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "ulist")
    r = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert "items" in r.json()["data"]


@pytest.mark.asyncio
async def test_admin_update_role(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "role")
    _, uid = await _make_user(db_session, client, "role")
    r = await client.put(
        f"/api/admin/users/{uid}/role",
        json={"role": "host"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    user = await db_session.get(User, uid)
    assert user.role == "host"


@pytest.mark.asyncio
async def test_admin_update_role_invalid(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "roleinv")
    _, uid = await _make_user(db_session, client, "roleinv")
    r = await client.put(
        f"/api/admin/users/{uid}/role",
        json={"role": "superadmin"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_delete_user(client: AsyncClient, db_session: AsyncSession):
    t = await _make_admin(db_session, client, "del")
    _, uid = await _make_user(db_session, client, "del")
    r = await client.delete(f"/api/admin/users/{uid}", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_admin_forbidden_non_admin(client: AsyncClient, db_session: AsyncSession):
    _, uid = await _make_user(db_session, client, "forbid")
    t = (
        await client.post(
            "/api/auth/login", json={"email": "user_forbid@test.com", "password": "Test1234!"}
        )
    ).json()["data"]["access_token"]
    r = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 403
