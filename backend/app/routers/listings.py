from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
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
from app.services.listing_photo import add_photo, delete_photo, list_photos
from app.services.user import get_user_by_id

router = APIRouter()


@router.get("/search", response_model=BaseResponse)
async def search(
    city: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    guests: int | None = Query(None, ge=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    listings = await search_listings(db, city, min_price, max_price, guests, page, size)
    return BaseResponse(
        success=True,
        data=[ListingResponse.model_validate(lst) for lst in listings],
    )


@router.get("/{listing_id}", response_model=BaseResponse)
async def detail(listing_id: str, db: AsyncSession = Depends(get_db)):
    listing = await get_listing(db, listing_id)
    return BaseResponse(success=True, data=ListingResponse.model_validate(listing))


@router.post("/", response_model=BaseResponse, status_code=201)
async def create(
    data: ListingCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await create_listing(db, user_id, data)
    listing = await get_listing(db, listing.id)
    return BaseResponse(success=True, data=ListingResponse.model_validate(listing))


@router.put("/{listing_id}", response_model=BaseResponse)
async def update(
    listing_id: str,
    data: ListingUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await update_listing(db, listing_id, user_id, data)
    return BaseResponse(success=True, data=ListingResponse.model_validate(listing))


@router.delete("/{listing_id}", response_model=BaseResponse)
async def delete(
    listing_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_listing(db, listing_id, user_id)
    return BaseResponse(success=True, message="已删除")


@router.get("/{listing_id}/photos", response_model=BaseResponse)
async def get_photos(listing_id: str, db: AsyncSession = Depends(get_db)):
    photos = await list_photos(db, listing_id)
    return BaseResponse(
        success=True,
        data=[ListingPhotoResponse.model_validate(p) for p in photos],
    )


@router.post("/{listing_id}/photos", response_model=BaseResponse, status_code=201)
async def upload_photo(
    listing_id: str,
    url: str = Query(...),
    is_primary: bool = Query(False),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    photo = await add_photo(db, listing_id, url, is_primary, user_id)
    return BaseResponse(success=True, data=ListingPhotoResponse.model_validate(photo))


@router.delete("/{listing_id}/photos/{photo_id}", response_model=BaseResponse)
async def remove_photo(
    photo_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_photo(db, photo_id, user_id)
    return BaseResponse(success=True, message="已删除")


@router.post("/{listing_id}/approve", response_model=BaseResponse)
async def approve(
    listing_id: str,
    data: ApprovalRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if user.role != "admin":
        raise ForbiddenException()
    if data.action == "approve":
        await approve_listing(db, listing_id)
    else:
        await reject_listing(db, listing_id)
    listing = await get_listing(db, listing_id)
    return BaseResponse(success=True, data=ListingResponse.model_validate(listing))
