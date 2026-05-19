import pytest
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_send_message(client: AsyncClient, db_session: AsyncSession):
    reg1 = await client.post(
        "/api/auth/register",
        json={"username": "sender", "email": "sender@test.com", "password": "Test1234!"},
    )
    token1 = reg1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "receiver", "email": "receiver@test.com", "password": "Test1234!"},
    )
    uid2 = (
        (await db_session.execute(select(User).where(User.email == "receiver@test.com")))
        .scalar_one()
        .id
    )
    resp = await client.post(
        "/api/messages/send",
        json={"receiver_id": uid2, "content": "Hello!"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["content"] == "Hello!"


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, db_session: AsyncSession):
    reg1 = await client.post(
        "/api/auth/register",
        json={"username": "conv1", "email": "conv1@test.com", "password": "Test1234!"},
    )
    token1 = reg1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "conv2", "email": "conv2@test.com", "password": "Test1234!"},
    )
    uid2 = (
        (await db_session.execute(select(User).where(User.email == "conv2@test.com")))
        .scalar_one()
        .id
    )
    await client.post(
        "/api/messages/send",
        json={"receiver_id": uid2, "content": "Hi"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    resp = await client.get(
        "/api/messages/conversations", headers={"Authorization": f"Bearer {token1}"}
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_get_messages(client: AsyncClient, db_session: AsyncSession):
    reg1 = await client.post(
        "/api/auth/register",
        json={"username": "msg1", "email": "msg1@test.com", "password": "Test1234!"},
    )
    token1 = reg1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "msg2", "email": "msg2@test.com", "password": "Test1234!"},
    )
    uid2 = (
        (await db_session.execute(select(User).where(User.email == "msg2@test.com")))
        .scalar_one()
        .id
    )
    await client.post(
        "/api/messages/send",
        json={"receiver_id": uid2, "content": "Hey"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    convs = await client.get(
        "/api/messages/conversations", headers={"Authorization": f"Bearer {token1}"}
    )
    conv_id = convs.json()["data"][0]["id"]
    resp = await client.get(
        f"/api/messages/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_mark_read(client: AsyncClient, db_session: AsyncSession):
    reg1 = await client.post(
        "/api/auth/register",
        json={"username": "mark1", "email": "mark1@test.com", "password": "Test1234!"},
    )
    token1 = reg1.json()["data"]["access_token"]
    await client.post(
        "/api/auth/register",
        json={"username": "mark2", "email": "mark2@test.com", "password": "Test1234!"},
    )
    uid2 = (
        (await db_session.execute(select(User).where(User.email == "mark2@test.com")))
        .scalar_one()
        .id
    )
    await client.post(
        "/api/messages/send",
        json={"receiver_id": uid2, "content": "Test"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    convs = await client.get(
        "/api/messages/conversations", headers={"Authorization": f"Bearer {token1}"}
    )
    conv_id = convs.json()["data"][0]["id"]
    resp = await client.post(
        f"/api/messages/conversations/{conv_id}/read", headers={"Authorization": f"Bearer {token1}"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_message_no_auth(client: AsyncClient):
    resp = await client.post("/api/messages/send", json={"receiver_id": "x", "content": "x"})
    assert resp.status_code == 401
