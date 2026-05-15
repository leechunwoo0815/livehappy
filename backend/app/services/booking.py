from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, Payment
from app.models.listing import Listing
from app.schemas.booking import BookingCreate

PLATFORM_FEE_RATE = Decimal("0.10")


async def create_booking(db: AsyncSession, guest_id: str, data: BookingCreate) -> Booking:
    if data.check_in >= data.check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="入住日期必须早于退房日期"
        )
    if data.check_in < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能预订过去的日期")

    listing = await db.get(Listing, data.listing_id)
    if not listing or not listing.is_active or listing.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源不存在或不可预订")
    if data.guests > listing.max_guests:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="超出最大入住人数")

    nights = (data.check_out - data.check_in).days
    total_price = Decimal(str(listing.price_per_night)) * Decimal(nights)

    booking = Booking(
        listing_id=data.listing_id,
        guest_id=guest_id,
        host_id=listing.host_id,
        check_in=data.check_in,
        check_out=data.check_out,
        guests=data.guests,
        total_price=total_price,
        status="pending",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def pay_booking(db: AsyncSession, booking_id: str, user_id: str) -> Payment:
    booking = await db.get(Booking, booking_id)
    if not booking or booking.guest_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if booking.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="订单状态不允许支付")

    amount = booking.total_price
    platform_fee = (amount * PLATFORM_FEE_RATE).quantize(Decimal("0.01"))
    host_payout = amount - platform_fee

    booking.status = "confirmed"
    booking.paid_at = datetime.now(UTC)

    payment = Payment(
        booking_id=booking_id,
        amount=amount,
        platform_fee=platform_fee,
        host_payout=host_payout,
        status="paid",
        paid_at=booking.paid_at,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def cancel_booking(
    db: AsyncSession, booking_id: str, user_id: str, reason: str | None = None
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if booking.guest_id != user_id and booking.host_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if booking.status in ("cancelled", "completed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="订单已结束")

    booking.status = "cancelled"
    booking.cancelled_at = datetime.now(UTC)
    booking.cancel_reason = reason

    if booking.status == "confirmed":
        payment = await _get_payment(db, booking_id)
        if payment:
            payment.status = "refunded"
            payment.refunded_at = booking.cancelled_at
            amount = payment.amount
            payment.amount = Decimal("0")
            payment.host_payout = Decimal("0")
            payment.platform_fee = Decimal("0")

    await db.commit()


async def get_user_bookings(db: AsyncSession, user_id: str, role: str = "guest") -> list[Booking]:
    if role == "host":
        result = await db.execute(
            select(Booking).where(Booking.host_id == user_id).order_by(Booking.created_at.desc())
        )
    else:
        result = await db.execute(
            select(Booking).where(Booking.guest_id == user_id).order_by(Booking.created_at.desc())
        )
    return list(result.scalars().all())


async def _get_payment(db: AsyncSession, booking_id: str) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.booking_id == booking_id))
    return result.scalar_one_or_none()
