import uuid

from sqlalchemy import ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    booking_id: Mapped[str] = mapped_column(String(36), unique=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply: Mapped[str | None] = mapped_column(Text, nullable=True)
