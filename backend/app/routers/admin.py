import asyncio
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
)
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.booking import Booking
from app.models.listing import Listing
from app.models.user import User
from app.schemas.common import BaseResponse

router = APIRouter()


async def _log_audit(
    db: AsyncSession,
    admin_id: str,
    action: str,
    target_type: str,
    target_id: str,
    detail: str | None = None,
):
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(log)


_seed_running = False


async def _require_admin(db: AsyncSession, user_id: str):
    user = await db.get(User, user_id)
    if not user or user.role != "admin":
        raise ForbiddenException()
    return user


@router.get("/stats", response_model=BaseResponse)
async def get_stats(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)

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

    return BaseResponse(
        success=True,
        data={
            "total_users": total_users or 0,
            "total_listings": total_listings or 0,
            "pending_listings": pending or 0,
            "total_bookings": total_bookings or 0,
            "revenue": float(revenue or 0),
        },
    )


@router.get("/listings", response_model=BaseResponse)
async def admin_list_listings(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)

    query = select(Listing).where(Listing.is_active.is_(True))
    if status_filter:
        query = query.where(Listing.status == status_filter)
    query = query.order_by(Listing.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(func.count(Listing.id)).where(Listing.is_active.is_(True))
    if status_filter:
        count_query = count_query.where(Listing.status == status_filter)
    total = (await db.execute(count_query)).scalar()

    return BaseResponse(
        success=True,
        data={
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
        },
    )


@router.get("/users", response_model=BaseResponse)
async def admin_list_users(
    role_filter: str | None = Query(None, alias="role"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)

    query = select(User)
    if role_filter:
        query = query.where(User.role == role_filter)
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    count_query = select(func.count(User.id))
    if role_filter:
        count_query = count_query.where(User.role == role_filter)
    total = (await db.execute(count_query)).scalar()

    return BaseResponse(
        success=True,
        data={
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
        },
    )


@router.get("/listings/pending", response_model=BaseResponse)
async def admin_pending_listings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)
    query = (
        select(Listing)
        .where(Listing.is_active.is_(True), Listing.status == "pending")
        .order_by(Listing.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    total = (
        await db.execute(
            select(func.count(Listing.id)).where(
                Listing.is_active.is_(True), Listing.status == "pending"
            )
        )
    ).scalar()

    return BaseResponse(
        success=True,
        data={
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
        },
    )


@router.post("/listings/{listing_id}/offline", response_model=BaseResponse)
async def admin_offline_listing(
    listing_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, admin_id)
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise NotFoundException()
    listing.is_active = False
    await _log_audit(
        db, admin_id, "offline_listing", "listing", listing_id, f"房源「{listing.title}」已下架"
    )
    await db.commit()
    return BaseResponse(success=True, message="房源已下架")


@router.post("/users/{target_user_id}/ban", response_model=BaseResponse)
async def admin_ban_user(
    target_user_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, admin_id)
    user = await db.get(User, target_user_id)
    if not user:
        raise NotFoundException()
    if user.role == "admin":
        raise BadRequestException("不能封禁管理员")
    user.is_active = False
    await _log_audit(
        db, admin_id, "ban_user", "user", target_user_id, f"用户「{user.username}」已被封禁"
    )
    await db.commit()
    return BaseResponse(success=True, message="用户已封禁")


@router.post("/users/{target_user_id}/unban", response_model=BaseResponse)
async def admin_unban_user(
    target_user_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, admin_id)
    user = await db.get(User, target_user_id)
    if not user:
        raise NotFoundException()
    user.is_active = True
    await _log_audit(
        db, admin_id, "unban_user", "user", target_user_id, f"用户「{user.username}」已解封"
    )
    await db.commit()
    return BaseResponse(success=True, message="用户已解封")


@router.get("/audit-logs", response_model=BaseResponse)
async def admin_audit_logs(
    action_filter: str | None = Query(None, alias="action"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action_filter:
        query = query.where(AuditLog.action == action_filter)
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(func.count(AuditLog.id))
    if action_filter:
        count_query = count_query.where(AuditLog.action == action_filter)
    total = (await db.execute(count_query)).scalar()

    return BaseResponse(
        success=True,
        data={
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
        },
    )


@router.get("/bookings", response_model=BaseResponse)
async def admin_bookings(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, user_id)
    query = select(Booking).order_by(Booking.created_at.desc())
    if status_filter:
        query = query.where(Booking.status == status_filter)
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(func.count(Booking.id))
    if status_filter:
        count_query = count_query.where(Booking.status == status_filter)
    total = (await db.execute(count_query)).scalar()

    return BaseResponse(
        success=True,
        data={
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
        },
    )


@router.put("/users/{user_id}/role", response_model=BaseResponse)
async def admin_update_user_role(
    user_id: str,
    role: str = Body(..., embed=True),
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, admin_id)
    if role not in ("user", "host", "admin"):
        raise BadRequestException("无效角色")
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException()
    user.role = role
    await db.commit()
    return BaseResponse(success=True, message="角色已更新")


@router.delete("/users/{user_id}", response_model=BaseResponse)
async def admin_delete_user(
    user_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, admin_id)
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException()
    await db.delete(user)
    await db.commit()
    return BaseResponse(success=True, message="用户已删除")


@router.post("/seed", response_model=BaseResponse)
async def admin_seed(
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    global _seed_running
    await _require_admin(db, admin_id)
    if _seed_running:
        raise RateLimitException("Seed already running")
    script = Path("/app/scripts/seed.py")
    if not script.exists():
        raise NotFoundException("Seed script not found")
    _seed_running = True

    async def _run():
        global _seed_running
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                str(script),
            )
            await proc.wait()
        finally:
            _seed_running = False

    background_tasks.add_task(_run)
    return BaseResponse(success=True, message="Seed started in background")


@router.get("/seed/status", response_model=BaseResponse)
async def admin_seed_status(
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_admin(db, admin_id)
    return BaseResponse(success=True, data={"running": _seed_running})
