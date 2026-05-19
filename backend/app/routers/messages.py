from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.schemas.message import (
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
)
from app.services.message import (
    get_conversations,
    get_messages,
    get_total_unread_count,
    mark_conversation_read,
    send_message,
)

router = APIRouter()

active_connections: dict[str, WebSocket] = {}


@router.get("/conversations", response_model=BaseResponse)
async def list_conversations(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convs = await get_conversations(db, user_id)
    return BaseResponse(
        success=True,
        data=[ConversationResponse.model_validate(c) for c in convs],
    )


@router.get("/conversations/{conv_id}/messages", response_model=BaseResponse)
async def list_messages(
    conv_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await get_messages(db, conv_id, user_id)
    return BaseResponse(
        success=True,
        data=[MessageResponse.model_validate(m) for m in messages],
    )


@router.get("/unread-count", response_model=BaseResponse)
async def unread_count(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await get_total_unread_count(db, user_id)
    return BaseResponse(success=True, data={"unread_count": count})


@router.post("/send", response_model=BaseResponse, status_code=201)
async def send(
    data: SendMessageRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = await send_message(db, user_id, data.receiver_id, data.content)
    ws = active_connections.get(data.receiver_id)
    if ws:
        try:
            await ws.send_json(
                {
                    "type": "new_message",
                    "conversation_id": msg.conversation_id,
                    "sender_id": user_id,
                    "content": data.content,
                }
            )
        except Exception:
            active_connections.pop(data.receiver_id, None)
    return BaseResponse(success=True, data=MessageResponse.model_validate(msg))


@router.post("/conversations/{conv_id}/read", response_model=BaseResponse)
async def mark_read(
    conv_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_conversation_read(db, conv_id, user_id)
    return BaseResponse(success=True, message="已读")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None or payload.get("type") != "access":
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
