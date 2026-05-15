from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ListingPhotoResponse(BaseModel):
    id: str
    url: str
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


class ListingCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    city: str = Field(..., max_length=100)
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_per_night: Decimal = Field(..., gt=0)
    bedrooms: int | None = None
    bathrooms: int | None = None
    max_guests: int = Field(default=1, ge=1)
    cover_image: str | None = None


class ListingUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    city: str | None = Field(None, max_length=100)
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_per_night: Decimal | None = Field(None, gt=0)
    bedrooms: int | None = None
    bathrooms: int | None = None
    max_guests: int | None = Field(None, ge=1)
    cover_image: str | None = None


class ListingResponse(BaseModel):
    id: str
    host_id: str
    title: str
    description: str | None
    city: str
    address: str | None
    latitude: float | None
    longitude: float | None
    price_per_night: float
    bedrooms: int | None
    bathrooms: int | None
    max_guests: int
    status: str
    cover_image: str | None
    is_active: bool
    created_at: datetime
    photos: list[ListingPhotoResponse] = []

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    reason: str | None = None
