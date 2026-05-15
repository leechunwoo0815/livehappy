from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    CancelRequest,
    PaymentResponse,
)
from app.services.booking import (
    cancel_booking,
    create_booking,
    get_user_bookings,
    pay_booking,
)

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=201)
async def create(
    data: BookingCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_booking(db, user_id, data)


@router.get("/", response_model=list[BookingResponse])
async def list_bookings(
    role: str = Query("guest", pattern="^(guest|host)$"),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_bookings(db, user_id, role)


@router.post("/{booking_id}/pay", response_model=PaymentResponse)
async def pay(
    booking_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await pay_booking(db, booking_id, user_id)


@router.post("/{booking_id}/cancel")
async def cancel(
    booking_id: str,
    data: CancelRequest = CancelRequest(),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await cancel_booking(db, booking_id, user_id, data.reason)
    return {"status": "cancelled"}
