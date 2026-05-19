"""
密码哈希、JWT Token 生成、Token 黑名单与 Redis 存储。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.config import settings
from app.redis import get_redis


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, role: str = "user") -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def store_refresh_token(user_id: str, jti: str) -> None:
    redis = get_redis()
    key = f"refresh:{user_id}"
    await redis.set(key, jti, ex=settings.jwt_refresh_token_expire_days * 86400)


async def revoke_refresh_token(user_id: str) -> None:
    redis = get_redis()
    await redis.delete(f"refresh:{user_id}")


async def get_stored_refresh_jti(user_id: str) -> str | None:
    redis = get_redis()
    return await redis.get(f"refresh:{user_id}")


async def blacklist_token(jti: str, expire_seconds: int) -> None:
    redis = get_redis()
    await redis.set(f"blacklist:{jti}", "1", ex=expire_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    redis = get_redis()
    result = await redis.get(f"blacklist:{jti}")
    return result is not None
