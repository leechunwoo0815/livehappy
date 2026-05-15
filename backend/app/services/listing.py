from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.listing import Listing
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return listing


async def search_listings(
    db: AsyncSession,
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    guests: int | None = None,
    page: int = 1,
    size: int = 20,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if listing.host_id != host_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(listing, key, value)
    await db.commit()
    await db.refresh(listing)
    return listing


async def delete_listing(db: AsyncSession, listing_id: str, host_id: str):
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if listing.host_id != host_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    listing.is_active = False
    await db.commit()


async def approve_listing(db: AsyncSession, listing_id: str):
    await db.execute(update(Listing).where(Listing.id == listing_id).values(status="approved"))
    await db.commit()


async def reject_listing(db: AsyncSession, listing_id: str):
    await db.execute(update(Listing).where(Listing.id == listing_id).values(status="rejected"))
    await db.commit()
