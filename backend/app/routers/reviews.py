from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.booking import Booking
from app.models.review import Review

router = APIRouter()


@router.post("/")
async def create_review(
    listing_id: str,
    booking_id: str,
    rating: int,
    content: str | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="评分需在1-5之间")
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if booking.status != "confirmed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能评价已完成的订单")
    result = await db.execute(select(Review).where(Review.booking_id == booking_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已评价")
    review = Review(
        listing_id=listing_id,
        booking_id=booking_id,
        user_id=user_id,
        rating=rating,
        content=content,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return {"id": review.id, "rating": review.rating, "content": review.content}


@router.get("/listing/{listing_id}")
async def list_reviews(listing_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.listing_id == listing_id).order_by(Review.created_at.desc())
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "rating": r.rating,
            "content": r.content,
            "reply": r.reply,
            "created_at": str(r.created_at),
        }
        for r in result.scalars().all()
    ]
