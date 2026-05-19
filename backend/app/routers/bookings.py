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
from app.schemas.common import BaseResponse
from app.services.booking import (
    cancel_booking,
    create_booking,
    get_booking_detail,
    get_user_bookings,
    pay_booking,
)

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=201)
async def create(
    data: BookingCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await create_booking(db, user_id, data)
    return BaseResponse(success=True, data=BookingResponse.model_validate(booking))


@router.get("/", response_model=BaseResponse)
async def list_bookings(
    role: str = Query("guest", pattern="^(guest|host)$"),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookings = await get_user_bookings(db, user_id, role)
    return BaseResponse(
        success=True,
        data=[BookingResponse.model_validate(b) for b in bookings],
    )


@router.get("/{booking_id}", response_model=BaseResponse)
async def detail(
    booking_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_booking_detail(db, booking_id, user_id)
    return BaseResponse(success=True, data=data)


@router.post("/{booking_id}/pay", response_model=BaseResponse)
async def pay(
    booking_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment = await pay_booking(db, booking_id, user_id)
    return BaseResponse(success=True, data=PaymentResponse.model_validate(payment))


@router.post("/{booking_id}/cancel", response_model=BaseResponse)
async def cancel(
    booking_id: str,
    data: CancelRequest = CancelRequest(),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await cancel_booking(db, booking_id, user_id, data.reason)
    return BaseResponse(success=True, message="已取消")
