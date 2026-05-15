from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.listing import ListingPhoto
from app.schemas.listing import (
    ApprovalRequest,
    ListingCreate,
    ListingPhotoResponse,
    ListingResponse,
    ListingUpdate,
)
from app.services.listing import (
    approve_listing,
    create_listing,
    delete_listing,
    get_listing,
    reject_listing,
    search_listings,
    update_listing,
)
from app.services.listing_photo import add_photo, delete_photo

router = APIRouter()


@router.get("/search", response_model=list[ListingResponse])
async def search(
    city: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    guests: int | None = Query(None, ge=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await search_listings(db, city, min_price, max_price, guests, page, size)


@router.get("/{listing_id}", response_model=ListingResponse)
async def detail(listing_id: str, db: AsyncSession = Depends(get_db)):
    return await get_listing(db, listing_id)


@router.post("/", response_model=ListingResponse, status_code=201)
async def create(
    data: ListingCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await create_listing(db, user_id, data)
    return await get_listing(db, listing.id)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update(
    listing_id: str,
    data: ListingUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_listing(db, listing_id, user_id, data)


@router.delete("/{listing_id}", status_code=204)
async def delete(
    listing_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_listing(db, listing_id, user_id)


@router.get("/{listing_id}/photos", response_model=list[ListingPhotoResponse])
async def list_photos(listing_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ListingPhoto)
        .where(ListingPhoto.listing_id == listing_id)
        .order_by(ListingPhoto.sort_order)
    )
    return result.scalars().all()


@router.post("/{listing_id}/photos", response_model=ListingPhotoResponse, status_code=201)
async def upload_photo(
    listing_id: str,
    url: str = Query(...),
    is_primary: bool = Query(False),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await add_photo(db, listing_id, url, is_primary, user_id)


@router.delete("/{listing_id}/photos/{photo_id}", status_code=204)
async def remove_photo(
    photo_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_photo(db, photo_id, user_id)


@router.post("/{listing_id}/approve", response_model=ListingResponse)
async def approve(
    listing_id: str,
    data: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    if data.action == "approve":
        await approve_listing(db, listing_id)
    else:
        await reject_listing(db, listing_id)
    return await get_listing(db, listing_id)
