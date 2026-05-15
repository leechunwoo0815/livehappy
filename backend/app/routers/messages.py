from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.message import (
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
)
from app.services.message import (
    get_conversations,
    get_messages,
    mark_conversation_read,
    send_message,
)

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_conversations(db, user_id)


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conv_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_messages(db, conv_id, user_id)


@router.post("/send", response_model=MessageResponse, status_code=201)
async def send(
    data: SendMessageRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await send_message(db, user_id, data.receiver_id, data.content)


@router.post("/conversations/{conv_id}/read")
async def mark_read(
    conv_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_conversation_read(db, conv_id, user_id)
    return {"status": "ok"}
