from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
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
        raise NotFoundException()
    if user_id not in (conv.participant_one, conv.participant_two):
        raise ForbiddenException()
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def mark_conversation_read(db: AsyncSession, conversation_id: str, user_id: str) -> None:
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise NotFoundException()
    if user_id not in (conv.participant_one, conv.participant_two):
        raise ForbiddenException()
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


async def get_total_unread_count(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(Conversation).where(
            or_(Conversation.participant_one == user_id, Conversation.participant_two == user_id)
        )
    )
    conversations = result.scalars().all()
    total = 0
    for conv in conversations:
        if user_id == conv.participant_one:
            total += conv.unread_count_one
        else:
            total += conv.unread_count_two
    return total


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
    try:
        await db.commit()
        await db.refresh(conv)
    except IntegrityError:
        await db.rollback()
        # Another request created the conversation concurrently — fetch it
        result = await db.execute(
            select(Conversation).where(
                or_(
                    (Conversation.participant_one == user_a)
                    & (Conversation.participant_two == user_b),
                    (Conversation.participant_one == user_b)
                    & (Conversation.participant_two == user_a),
                )
            )
        )
        conv = result.scalar_one()
    return conv
