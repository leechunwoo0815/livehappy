from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing, ListingPhoto


async def add_photo(
    db: AsyncSession,
    listing_id: str,
    url: str,
    is_primary: bool,
    user_id: str,
) -> ListingPhoto:
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if listing.host_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if is_primary:
        await _unset_primary(db, listing_id)
    photo = ListingPhoto(listing_id=listing_id, url=url, is_primary=is_primary)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


async def delete_photo(db: AsyncSession, photo_id: str, user_id: str):
    result = await db.execute(select(ListingPhoto).where(ListingPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    listing = await db.get(Listing, photo.listing_id)
    if not listing or listing.host_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    await db.delete(photo)
    await db.commit()


async def _unset_primary(db: AsyncSession, listing_id: str):
    await db.execute(
        update(ListingPhoto)
        .where(ListingPhoto.listing_id == listing_id, ListingPhoto.is_primary.is_(True))
        .values(is_primary=False)
    )
    await db.commit()
