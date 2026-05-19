import pytest
from app.models.notification import Notification
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient, user_headers: dict):
    r = await client.get("/api/notifications/", headers=user_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["items"] == []
    assert data["unread_count"] == 0


@pytest.mark.asyncio
async def test_list_notifications_with_data(
    client: AsyncClient, user_headers: dict, db_session: AsyncSession
):
    # Create notification directly in DB
    from app.config import settings
    from jose import jwt as jose_jwt

    token = user_headers["Authorization"].split()[1]
    payload = jose_jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    uid = payload["sub"]

    notif = Notification(user_id=uid, type="booking_confirmed", content="Your booking is confirmed")
    db_session.add(notif)
    await db_session.commit()

    r = await client.get("/api/notifications/", headers=user_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["items"]) == 1
    assert data["unread_count"] == 1
    assert data["items"][0]["type"] == "booking_confirmed"


@pytest.mark.asyncio
async def test_mark_notification_as_read(
    client: AsyncClient, user_headers: dict, db_session: AsyncSession
):
    from app.config import settings
    from jose import jwt as jose_jwt

    token = user_headers["Authorization"].split()[1]
    payload = jose_jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    uid = payload["sub"]

    notif = Notification(user_id=uid, type="test", content="test content")
    db_session.add(notif)
    await db_session.commit()
    await db_session.refresh(notif)

    r = await client.post(f"/api/notifications/{notif.id}/read", headers=user_headers)
    assert r.status_code == 200

    # Verify unread count dropped
    r2 = await client.get("/api/notifications/", headers=user_headers)
    assert r2.json()["data"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read(
    client: AsyncClient, user_headers: dict, db_session: AsyncSession
):
    from app.config import settings
    from jose import jwt as jose_jwt

    token = user_headers["Authorization"].split()[1]
    payload = jose_jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    uid = payload["sub"]

    for i in range(3):
        db_session.add(Notification(user_id=uid, type="test", content=f"msg {i}"))
    await db_session.commit()

    r = await client.post("/api/notifications/read-all", headers=user_headers)
    assert r.status_code == 200

    r2 = await client.get("/api/notifications/", headers=user_headers)
    assert r2.json()["data"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_notification_not_found(client: AsyncClient, user_headers: dict):
    r = await client.post("/api/notifications/nonexistent/read", headers=user_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_notifications_unauthorized(client: AsyncClient):
    r = await client.get("/api/notifications/")
    assert r.status_code == 401
