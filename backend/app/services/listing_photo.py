from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.listing import Listing, ListingPhoto


async def list_photos(db: AsyncSession, listing_id: str) -> list[ListingPhoto]:
    result = await db.execute(
        select(ListingPhoto)
        .where(ListingPhoto.listing_id == listing_id)
        .order_by(ListingPhoto.sort_order)
    )
    return list(result.scalars().all())


async def add_photo(
    db: AsyncSession,
    listing_id: str,
    url: str,
    is_primary: bool,
    user_id: str,
) -> ListingPhoto:
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise NotFoundException()
    if listing.host_id != user_id:
        raise ForbiddenException()
    if is_primary:
        await _unset_primary(db, listing_id)
    photo = ListingPhoto(listing_id=listing_id, url=url, is_primary=is_primary)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


async def delete_photo(db: AsyncSession, photo_id: str, user_id: str) -> None:
    result = await db.execute(select(ListingPhoto).where(ListingPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise NotFoundException()
    listing = await db.get(Listing, photo.listing_id)
    if not listing or listing.host_id != user_id:
        raise ForbiddenException()
    await db.delete(photo)
    await db.commit()


async def _unset_primary(db: AsyncSession, listing_id: str) -> None:
    await db.execute(
        update(ListingPhoto)
        .where(ListingPhoto.listing_id == listing_id, ListingPhoto.is_primary.is_(True))
        .values(is_primary=False)
    )
    await db.flush()
