from datetime import date, datetime

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    listing_id: str
    check_in: date
    check_out: date
    guests: int = Field(default=1, ge=1)


class BookingResponse(BaseModel):
    id: str
    listing_id: str
    guest_id: str
    host_id: str
    check_in: date
    check_out: date
    guests: int
    total_price: float
    status: str
    paid_at: datetime | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    amount: float
    platform_fee: float
    host_payout: float
    status: str
    paid_at: datetime | None

    model_config = {"from_attributes": True}


class CancelRequest(BaseModel):
    reason: str | None = None
