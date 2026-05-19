from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.listing import Listing
from app.models.review import Review
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingUpdate


async def create_listing(db: AsyncSession, host_id: str, data: ListingCreate) -> Listing:
    listing = Listing(host_id=host_id, **data.model_dump())
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


async def get_listing(db: AsyncSession, listing_id: str) -> Listing:
    result = await db.execute(
        select(Listing)
        .where(Listing.id == listing_id, Listing.is_active.is_(True))
        .options(selectinload(Listing.photos))
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise NotFoundException()
    return listing


async def get_listing_detail(db: AsyncSession, listing_id: str) -> dict:
    listing = await get_listing(db, listing_id)

    reviews_result = await db.execute(
        select(Review).where(Review.listing_id == listing_id).order_by(Review.created_at.desc())
    )
    reviews = reviews_result.scalars().all()

    avg_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.listing_id == listing_id)
    )
    avg_rating = avg_result.scalar()

    return {
        "id": listing.id,
        "host_id": listing.host_id,
        "title": listing.title,
        "description": listing.description,
        "city": listing.city,
        "address": listing.address,
        "price_per_night": listing.price_per_night,
        "max_guests": listing.max_guests,
        "status": listing.status,
        "cover_image": listing.cover_image,
        "is_active": listing.is_active,
        "photos": [
            {"id": p.id, "url": p.url, "is_primary": p.is_primary, "sort_order": p.sort_order}
            for p in listing.photos
        ],
        "reviews": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "rating": r.rating,
                "content": r.content,
                "reply": r.reply,
                "created_at": str(r.created_at),
            }
            for r in reviews
        ],
        "avg_rating": round(float(avg_rating), 1) if avg_rating else None,
        "review_count": len(reviews),
        "created_at": str(listing.created_at),
    }


async def search_listings(
    db: AsyncSession,
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    guests: int | None = None,
    page: int = 1,
    size: int = 20,
    sort_by: str | None = None,
) -> list[Listing]:
    query = (
        select(Listing)
        .where(Listing.status == "approved", Listing.is_active.is_(True))
        .options(selectinload(Listing.photos))
    )
    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    if min_price is not None:
        query = query.where(Listing.price_per_night >= min_price)
    if max_price is not None:
        query = query.where(Listing.price_per_night <= max_price)
    if guests is not None:
        query = query.where(Listing.max_guests >= guests)
    if sort_by == "price_asc":
        query = query.order_by(Listing.price_per_night.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Listing.price_per_night.desc())
    elif sort_by == "newest":
        query = query.order_by(Listing.created_at.desc())
    else:
        query = query.order_by(Listing.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_listing(
    db: AsyncSession, listing_id: str, host_id: str, data: ListingUpdate
) -> Listing:
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.photos))
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise NotFoundException()
    if listing.host_id != host_id:
        user = await db.get(User, host_id)
        if not user or user.role != "admin":
            raise ForbiddenException()
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(listing, key, value)
    await db.commit()
    await db.refresh(listing)
    return listing


async def delete_listing(db: AsyncSession, listing_id: str, host_id: str) -> None:
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise NotFoundException()
    if listing.host_id != host_id:
        user = await db.get(User, host_id)
        if not user or user.role != "admin":
            raise ForbiddenException()
    listing.is_active = False
    await db.commit()


async def approve_listing(db: AsyncSession, listing_id: str) -> None:
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise NotFoundException()
    if listing.status != "pending":
        raise BadRequestException("只能审核待审核的房源")
    listing.status = "approved"
    await db.commit()


async def reject_listing(db: AsyncSession, listing_id: str) -> None:
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise NotFoundException()
    if listing.status != "pending":
        raise BadRequestException("只能审核待审核的房源")
    listing.status = "rejected"
    await db.commit()
