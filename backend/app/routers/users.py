from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.schemas.user import UserResponse
from app.services.social import get_user_favorites
from app.services.user import get_user_by_id

router = APIRouter()


@router.get("/me", response_model=BaseResponse)
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    return BaseResponse(success=True, data=UserResponse.model_validate(user))


@router.get("/favorites", response_model=BaseResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_user_favorites(db, user_id, page, size)
    return BaseResponse(
        success=True,
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": size,
            "has_next": page * size < total,
        },
    )
