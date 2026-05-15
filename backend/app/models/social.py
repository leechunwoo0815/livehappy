import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)


class NoteComment(Base, TimestampMixin):
    __tablename__ = "note_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id: Mapped[str] = mapped_column(ForeignKey("notes.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    content: Mapped[str] = mapped_column(Text)


class NoteLike(Base, TimestampMixin):
    __tablename__ = "note_likes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id: Mapped[str] = mapped_column(ForeignKey("notes.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    __table_args__ = (UniqueConstraint("note_id", "user_id", name="uq_note_like"),)


class UserFollow(Base, TimestampMixin):
    __tablename__ = "user_follows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id: Mapped[str] = mapped_column(String(36), index=True)
    following_id: Mapped[str] = mapped_column(String(36), index=True)
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="uq_user_follow"),)
