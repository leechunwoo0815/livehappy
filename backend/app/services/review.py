from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException
from app.models.booking import Booking
from app.models.review import Review


async def create_review(
    db: AsyncSession,
    user_id: str,
    listing_id: str,
    booking_id: str,
    rating: int,
    content: str | None = None,
) -> dict:
    if not 1 <= rating <= 5:
        raise BadRequestException("评分需在1-5之间")
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != user_id:
        raise ForbiddenException()
    if booking.status != "completed":
        raise BadRequestException("只能评价已完成的订单")
    result = await db.execute(select(Review).where(Review.booking_id == booking_id))
    if result.scalar_one_or_none():
        raise ConflictException("已评价")
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


async def list_reviews(db: AsyncSession, listing_id: str) -> list[dict]:
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
