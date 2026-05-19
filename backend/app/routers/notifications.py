from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.schemas.notification import NotificationResponse
from app.services.notification import (
    get_unread_count,
    get_user_notifications,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter()


@router.get("/", response_model=BaseResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifs = await get_user_notifications(db, user_id, page, size)
    unread = await get_unread_count(db, user_id)
    return BaseResponse(
        success=True,
        data={
            "items": [NotificationResponse.model_validate(n) for n in notifs],
            "unread_count": unread,
        },
    )


@router.post("/{notification_id}/read", response_model=BaseResponse)
async def read_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_as_read(db, notification_id, user_id)
    return BaseResponse(success=True, message="已读")


@router.post("/read-all", response_model=BaseResponse)
async def read_all(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await mark_all_as_read(db, user_id)
    return BaseResponse(success=True, message="全部已读")
