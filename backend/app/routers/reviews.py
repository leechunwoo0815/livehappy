from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.services.review import create_review, list_reviews

router = APIRouter()


@router.post("/", response_model=BaseResponse)
async def create(
    listing_id: str,
    booking_id: str,
    rating: int,
    content: str | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await create_review(db, user_id, listing_id, booking_id, rating, content)
    return BaseResponse(success=True, data=result)


@router.get("/listing/{listing_id}", response_model=BaseResponse)
async def list(listing_id: str, db: AsyncSession = Depends(get_db)):
    reviews = await list_reviews(db, listing_id)
    return BaseResponse(success=True, data=reviews)
