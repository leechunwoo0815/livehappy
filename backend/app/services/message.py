from fastapi import HTTPException, status
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Conversation, Message


async def send_message(db: AsyncSession, sender_id: str, receiver_id: str, content: str) -> Message:
    conv = await _get_or_create_conversation(db, sender_id, receiver_id)
    msg = Message(conversation_id=conv.id, sender_id=sender_id, content=content)
    conv.last_message = content
    if sender_id == conv.participant_one:
        conv.unread_count_two += 1
    else:
        conv.unread_count_one += 1
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_conversations(db: AsyncSession, user_id: str) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(
            or_(Conversation.participant_one == user_id, Conversation.participant_two == user_id)
        )
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_messages(db: AsyncSession, conversation_id: str, user_id: str) -> list[Message]:
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if user_id not in (conv.participant_one, conv.participant_two):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def mark_conversation_read(db: AsyncSession, conversation_id: str, user_id: str):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if user_id not in (conv.participant_one, conv.participant_two):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    await db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.is_read.is_(False),
        )
        .values(is_read=True)
    )
    if user_id == conv.participant_one:
        conv.unread_count_one = 0
    else:
        conv.unread_count_two = 0
    await db.commit()


async def _get_or_create_conversation(db: AsyncSession, user_a: str, user_b: str) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            or_(
                (Conversation.participant_one == user_a) & (Conversation.participant_two == user_b),
                (Conversation.participant_one == user_b) & (Conversation.participant_two == user_a),
            )
        )
    )
    conv = result.scalar_one_or_none()
    if conv:
        return conv
    conv = Conversation(participant_one=user_a, participant_two=user_b)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv
