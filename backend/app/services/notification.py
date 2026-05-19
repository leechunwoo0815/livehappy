"""Notification business logic."""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.notification import Notification


async def get_user_notifications(
    db: AsyncSession, user_id: str, page: int = 1, size: int = 20
) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(result.scalars().all())


async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
    )
    return result.scalar() or 0


async def mark_as_read(db: AsyncSession, notification_id: str, user_id: str) -> None:
    notif = await db.get(Notification, notification_id)
    if not notif:
        raise NotFoundException()
    if notif.user_id != user_id:
        raise ForbiddenException()
    notif.is_read = True
    await db.commit()


async def mark_all_as_read(db: AsyncSession, user_id: str) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()


async def create_notification(
    db: AsyncSession,
    user_id: str,
    notif_type: str,
    content: str,
    related_id: str | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        content=content,
        related_id=related_id,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif
