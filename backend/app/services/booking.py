from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.booking import Booking, Payment
from app.models.listing import Listing
from app.schemas.booking import BookingCreate
from app.services.notification import create_notification

PLATFORM_FEE_RATE = Decimal("0.10")


async def create_booking(db: AsyncSession, guest_id: str, data: BookingCreate) -> Booking:
    if data.check_in >= data.check_out:
        raise BadRequestException("入住日期必须早于退房日期")
    if data.check_in < date.today():
        raise BadRequestException("不能预订过去的日期")

    listing = await db.get(Listing, data.listing_id)
    if not listing or not listing.is_active or listing.status != "approved":
        raise NotFoundException("房源不存在或不可预订")
    if data.guests > listing.max_guests:
        raise BadRequestException("超出最大入住人数")

    # Check for overlapping bookings on the same listing
    overlap = await db.execute(
        select(Booking).where(
            Booking.listing_id == data.listing_id,
            Booking.status.in_(["pending", "confirmed"]),
            Booking.check_in < data.check_out,
            Booking.check_out > data.check_in,
        )
    )
    if overlap.scalar_one_or_none():
        raise ConflictException("该房源在所选日期已被预订")

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
    result = await db.execute(select(Booking).where(Booking.id == booking_id).with_for_update())
    booking = result.scalar_one_or_none()
    if not booking or booking.guest_id != user_id:
        raise NotFoundException()
    if booking.status != "pending":
        raise BadRequestException("订单状态不允许支付")

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

    await create_notification(
        db,
        booking.host_id,
        "booking_confirmed",
        f"您有一笔新订单已支付，金额 ¥{amount}",
        booking_id,
    )

    return payment


async def cancel_booking(
    db: AsyncSession, booking_id: str, user_id: str, reason: str | None = None
) -> None:
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise NotFoundException()
    if user_id not in (booking.guest_id, booking.host_id):
        raise ForbiddenException()
    if booking.status in ("cancelled", "completed"):
        raise BadRequestException("订单已结束")

    was_confirmed = booking.status == "confirmed"
    booking.status = "cancelled"
    booking.cancelled_at = datetime.now(UTC)
    booking.cancel_reason = reason

    if was_confirmed:
        payment = await _get_payment(db, booking_id)
        if payment and payment.status == "paid":
            payment.status = "refunded"
            payment.refunded_at = booking.cancelled_at
            payment.amount = Decimal("0")
            payment.host_payout = Decimal("0")
            payment.platform_fee = Decimal("0")

    await db.commit()

    notify_user = booking.host_id if user_id == booking.guest_id else booking.guest_id
    await create_notification(
        db,
        notify_user,
        "booking_cancelled",
        "订单已取消" + (f"，原因：{reason}" if reason else ""),
        booking_id,
    )


async def get_booking(db: AsyncSession, booking_id: str, user_id: str) -> Booking:
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise NotFoundException()
    if user_id not in (booking.guest_id, booking.host_id):
        raise ForbiddenException()
    return booking


async def get_booking_detail(db: AsyncSession, booking_id: str, user_id: str) -> dict:
    booking = await get_booking(db, booking_id, user_id)
    listing = await db.get(Listing, booking.listing_id)
    return {
        "id": booking.id,
        "listing_id": booking.listing_id,
        "guest_id": booking.guest_id,
        "host_id": booking.host_id,
        "check_in": str(booking.check_in),
        "check_out": str(booking.check_out),
        "guests": booking.guests,
        "total_price": float(booking.total_price),
        "status": booking.status,
        "paid_at": str(booking.paid_at) if booking.paid_at else None,
        "cancelled_at": str(booking.cancelled_at) if booking.cancelled_at else None,
        "cancel_reason": booking.cancel_reason,
        "created_at": str(booking.created_at),
        "listing": {
            "id": listing.id,
            "title": listing.title,
            "city": listing.city,
            "address": listing.address,
            "price_per_night": float(listing.price_per_night),
            "cover_image": listing.cover_image,
        } if listing else None,
    }


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
