import pytest
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_note(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "noteuser", "email": "noteuser@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    resp = await client.post(
        "/api/social/notes",
        json={"title": "My Trip", "content": "Great!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "My Trip"


@pytest.mark.asyncio
async def test_list_notes(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "listnotes", "email": "listnotes@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    await client.post(
        "/api/social/notes",
        json={"title": "Post1", "content": "C1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/api/social/notes")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_like_note(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "liker", "email": "liker@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    c = await client.post("/api/social/notes", json={"title": "L", "content": "N"}, headers=h)
    nid = c.json()["data"]["id"]
    r = await client.post(f"/api/social/notes/{nid}/like", headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "liked"


@pytest.mark.asyncio
async def test_like_twice(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "dl", "email": "dl@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    c = await client.post("/api/social/notes", json={"title": "X", "content": "Y"}, headers=h)
    nid = c.json()["data"]["id"]
    await client.post(f"/api/social/notes/{nid}/like", headers=h)
    r = await client.post(f"/api/social/notes/{nid}/like", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_unlike_note(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "ul", "email": "ul@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    c = await client.post("/api/social/notes", json={"title": "A", "content": "B"}, headers=h)
    nid = c.json()["data"]["id"]
    await client.post(f"/api/social/notes/{nid}/like", headers=h)
    r = await client.post(f"/api/social/notes/{nid}/unlike", headers=h)
    assert r.status_code == 200 and r.json()["data"]["status"] == "unliked"


@pytest.mark.asyncio
async def test_add_comment(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "co", "email": "co@test.com", "password": "Test1234!"},
    )
    token = reg.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    c = await client.post("/api/social/notes", json={"title": "T", "content": "C"}, headers=h)
    nid = c.json()["data"]["id"]
    r = await client.post(f"/api/social/notes/{nid}/comments?content=Great!", headers=h)
    assert r.status_code == 200 and r.json()["data"]["content"] == "Great!"


@pytest.mark.asyncio
async def test_follow_user(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "f1", "email": "f1@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "f2", "email": "f2@test.com", "password": "Test1234!"},
    )
    u2 = (await db_session.execute(select(User).where(User.email == "f2@test.com"))).scalar_one().id
    r = await client.post(f"/api/social/follow/{u2}", headers={"Authorization": f"Bearer {t1}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_follow_self(client: AsyncClient, db_session: AsyncSession):
    r = await client.post(
        "/api/auth/register",
        json={"username": "sf", "email": "sf@test.com", "password": "Test1234!"},
    )
    token = r.json()["data"]["access_token"]
    uid = (
        (await db_session.execute(select(User).where(User.email == "sf@test.com"))).scalar_one().id
    )
    resp = await client.post(
        f"/api/social/follow/{uid}", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_unfollow_user(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "uf1", "email": "uf1@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "uf2", "email": "uf2@test.com", "password": "Test1234!"},
    )
    u2 = (
        (await db_session.execute(select(User).where(User.email == "uf2@test.com"))).scalar_one().id
    )
    await client.post(f"/api/social/follow/{u2}", headers={"Authorization": f"Bearer {t1}"})
    r = await client.post(f"/api/social/unfollow/{u2}", headers={"Authorization": f"Bearer {t1}"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_unfollow_not_following(client: AsyncClient, db_session: AsyncSession):
    r1 = await client.post(
        "/api/auth/register",
        json={"username": "unf1", "email": "unf1@test.com", "password": "Test1234!"},
    )
    t1 = r1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "unf2", "email": "unf2@test.com", "password": "Test1234!"},
    )
    u2 = (
        (await db_session.execute(select(User).where(User.email == "unf2@test.com")))
        .scalar_one()
        .id
    )
    r = await client.post(f"/api/social/unfollow/{u2}", headers={"Authorization": f"Bearer {t1}"})
    assert r.status_code == 404
