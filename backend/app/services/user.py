"""User query and mutation helpers used by routers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.services.auth import hash_password, verify_password


async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException()
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def change_password(
    db: AsyncSession, user_id: str, old_password: str, new_password: str
) -> None:
    user = await get_user_by_id(db, user_id)
    if not verify_password(old_password, user.password_hash):
        raise BadRequestException("原密码错误")
    user.password_hash = hash_password(new_password)
    await db.commit()
