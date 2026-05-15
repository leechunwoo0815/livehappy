import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    participant_one: Mapped[str] = mapped_column(String(36), index=True)
    participant_two: Mapped[str] = mapped_column(String(36), index=True)
    last_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    unread_count_one: Mapped[int] = mapped_column(Integer, default=0)
    unread_count_two: Mapped[int] = mapped_column(Integer, default=0)


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_id: Mapped[str] = mapped_column(String(36), index=True)
    content: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(default=False)
