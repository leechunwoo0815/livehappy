"""Admin business logic — stats, listing/user management, audit logs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.booking import Booking
from app.models.listing import Listing
from app.models.user import User
from app.redis import get_redis


async def require_admin(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if not user or user.role != "admin":
        raise ForbiddenException()
    return user


async def _log_audit(
    db: AsyncSession,
    admin_id: str,
    action: str,
    target_type: str,
    target_id: str,
    detail: str | None = None,
) -> None:
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(log)


async def get_platform_stats(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_listings = (
        await db.execute(select(func.count(Listing.id)).where(Listing.is_active.is_(True)))
    ).scalar()
    pending = (
        await db.execute(
            select(func.count(Listing.id)).where(
                Listing.status == "pending", Listing.is_active.is_(True)
            )
        )
    ).scalar()
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar()
    revenue = (
        await db.execute(
            select(func.coalesce(func.sum(Booking.total_price), 0)).where(
                Booking.status == "confirmed"
            )
        )
    ).scalar()
    return {
        "total_users": total_users or 0,
        "total_listings": total_listings or 0,
        "pending_listings": pending or 0,
        "total_bookings": total_bookings or 0,
        "revenue": float(revenue or 0),
    }


async def admin_list_listings(
    db: AsyncSession,
    status_filter: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    query = select(Listing).where(Listing.is_active.is_(True))
    if status_filter:
        query = query.where(Listing.status == status_filter)
    query = query.order_by(Listing.created_at.desc()).offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()

    count_query = select(func.count(Listing.id)).where(Listing.is_active.is_(True))
    if status_filter:
        count_query = count_query.where(Listing.status == status_filter)
    total = (await db.execute(count_query)).scalar()

    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "city": item.city,
                "price_per_night": item.price_per_night,
                "status": item.status,
                "host_id": item.host_id,
                "created_at": str(item.created_at),
            }
            for item in items
        ],
        "total": total or 0,
    }


async def admin_list_users(
    db: AsyncSession,
    role_filter: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    query = select(User)
    if role_filter:
        query = query.where(User.role == role_filter)
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    users = (await db.execute(query)).scalars().all()

    count_query = select(func.count(User.id))
    if role_filter:
        count_query = count_query.where(User.role == role_filter)
    total = (await db.execute(count_query)).scalar()

    return {
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "score": u.score,
                "created_at": str(u.created_at),
            }
            for u in users
        ],
        "total": total or 0,
    }


async def admin_pending_listings(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
) -> dict:
    query = (
        select(Listing)
        .where(Listing.is_active.is_(True), Listing.status == "pending")
        .order_by(Listing.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = (await db.execute(query)).scalars().all()

    total = (
        await db.execute(
            select(func.count(Listing.id)).where(
                Listing.is_active.is_(True), Listing.status == "pending"
            )
        )
    ).scalar()

    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "city": item.city,
                "price_per_night": item.price_per_night,
                "host_id": item.host_id,
                "created_at": str(item.created_at),
            }
            for item in items
        ],
        "total": total or 0,
    }


async def admin_offline_listing(db: AsyncSession, listing_id: str, admin_id: str) -> None:
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise NotFoundException()
    listing.is_active = False
    await _log_audit(
        db, admin_id, "offline_listing", "listing", listing_id, f"房源「{listing.title}」已下架"
    )
    await db.commit()


async def admin_ban_user(db: AsyncSession, target_user_id: str, admin_id: str) -> None:
    user = await db.get(User, target_user_id)
    if not user:
        raise NotFoundException()
    if user.role == "admin":
        raise BadRequestException("不能封禁管理员")
    user.is_banned = True
    try:
        redis = get_redis()
        await redis.sadd("banned_users", target_user_id)
    except RuntimeError:
        pass
    await _log_audit(
        db, admin_id, "ban_user", "user", target_user_id, f"用户「{user.username}」已被封禁"
    )
    await db.commit()


async def admin_unban_user(db: AsyncSession, target_user_id: str, admin_id: str) -> None:
    user = await db.get(User, target_user_id)
    if not user:
        raise NotFoundException()
    user.is_banned = False
    try:
        redis = get_redis()
        await redis.srem("banned_users", target_user_id)
    except RuntimeError:
        pass
    await _log_audit(
        db, admin_id, "unban_user", "user", target_user_id, f"用户「{user.username}」已解封"
    )
    await db.commit()


async def admin_update_user_role(db: AsyncSession, user_id: str, role: str, admin_id: str) -> None:
    if role not in ("user", "host", "admin"):
        raise BadRequestException("无效角色")
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException()
    user.role = role
    await db.commit()


async def admin_delete_user(db: AsyncSession, user_id: str, admin_id: str) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException()
    await db.delete(user)
    await db.commit()


async def admin_list_audit_logs(
    db: AsyncSession,
    action_filter: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action_filter:
        query = query.where(AuditLog.action == action_filter)
    query = query.offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()

    count_query = select(func.count(AuditLog.id))
    if action_filter:
        count_query = count_query.where(AuditLog.action == action_filter)
    total = (await db.execute(count_query)).scalar()

    return {
        "items": [
            {
                "id": item.id,
                "admin_id": item.admin_id,
                "action": item.action,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "detail": item.detail,
                "created_at": str(item.created_at),
            }
            for item in items
        ],
        "total": total or 0,
    }


async def admin_list_bookings(
    db: AsyncSession,
    status_filter: str | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    query = select(Booking).order_by(Booking.created_at.desc())
    if status_filter:
        query = query.where(Booking.status == status_filter)
    query = query.offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()

    count_query = select(func.count(Booking.id))
    if status_filter:
        count_query = count_query.where(Booking.status == status_filter)
    total = (await db.execute(count_query)).scalar()

    return {
        "items": [
            {
                "id": item.id,
                "listing_id": item.listing_id,
                "guest_id": item.guest_id,
                "host_id": item.host_id,
                "check_in": str(item.check_in),
                "check_out": str(item.check_out),
                "guests": item.guests,
                "total_price": str(item.total_price),
                "status": item.status,
                "created_at": str(item.created_at),
            }
            for item in items
        ],
        "total": total or 0,
    }
