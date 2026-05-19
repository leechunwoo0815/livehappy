import asyncio
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, RateLimitException
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.services.admin import (
    admin_ban_user,
    admin_delete_user,
    admin_list_audit_logs,
    admin_list_bookings,
    admin_list_listings,
    admin_list_users,
    admin_offline_listing,
    admin_pending_listings,
    admin_unban_user,
    admin_update_user_role,
    get_platform_stats,
    require_admin,
)

router = APIRouter()

_seed_running = False


@router.get("/stats", response_model=BaseResponse)
async def get_stats(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, user_id)
    data = await get_platform_stats(db)
    return BaseResponse(success=True, data=data)


@router.get("/listings", response_model=BaseResponse)
async def list_listings(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, user_id)
    data = await admin_list_listings(db, status_filter, page, size)
    return BaseResponse(success=True, data=data)


@router.get("/users", response_model=BaseResponse)
async def list_users(
    role_filter: str | None = Query(None, alias="role"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, user_id)
    data = await admin_list_users(db, role_filter, page, size)
    return BaseResponse(success=True, data=data)


@router.get("/listings/pending", response_model=BaseResponse)
async def pending_listings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, user_id)
    data = await admin_pending_listings(db, page, size)
    return BaseResponse(success=True, data=data)


@router.post("/listings/{listing_id}/offline", response_model=BaseResponse)
async def offline_listing(
    listing_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, admin_id)
    await admin_offline_listing(db, listing_id, admin_id)
    return BaseResponse(success=True, message="房源已下架")


@router.post("/users/{target_user_id}/ban", response_model=BaseResponse)
async def ban_user(
    target_user_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, admin_id)
    await admin_ban_user(db, target_user_id, admin_id)
    return BaseResponse(success=True, message="用户已封禁")


@router.post("/users/{target_user_id}/unban", response_model=BaseResponse)
async def unban_user(
    target_user_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, admin_id)
    await admin_unban_user(db, target_user_id, admin_id)
    return BaseResponse(success=True, message="用户已解封")


@router.get("/audit-logs", response_model=BaseResponse)
async def audit_logs(
    action_filter: str | None = Query(None, alias="action"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, user_id)
    data = await admin_list_audit_logs(db, action_filter, page, size)
    return BaseResponse(success=True, data=data)


@router.get("/bookings", response_model=BaseResponse)
async def bookings(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, user_id)
    data = await admin_list_bookings(db, status_filter, page, size)
    return BaseResponse(success=True, data=data)


@router.put("/users/{user_id}/role", response_model=BaseResponse)
async def update_user_role(
    user_id: str,
    role: str = Body(..., embed=True),
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, admin_id)
    await admin_update_user_role(db, user_id, role, admin_id)
    return BaseResponse(success=True, message="角色已更新")


@router.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, admin_id)
    await admin_delete_user(db, user_id, admin_id)
    return BaseResponse(success=True, message="用户已删除")


@router.post("/seed", response_model=BaseResponse)
async def seed(
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    global _seed_running
    await require_admin(db, admin_id)
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
async def seed_status(
    admin_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_admin(db, admin_id)
    return BaseResponse(success=True, data={"running": _seed_running})
