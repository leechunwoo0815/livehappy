"""Redis client with in-memory fallback for local development.

When Redis is unavailable (no Docker), falls back to a dict-based implementation
so the app works without any external service.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis as AsyncRedis

_real_redis: AsyncRedis | None = None
_fallback: _InMemoryRedis | None = None


class _InMemoryRedis:
    def __init__(self):
        self._store: dict[str, str] = {}
        self._set_store: dict[str, set[str]] = {}
        self._expiry: dict[str, float] = {}

    def _purge(self):
        now = time.time()
        expired = [k for k, t in self._expiry.items() if t <= now]
        for k in expired:
            self._store.pop(k, None)
            self._expiry.pop(k, None)

    async def get(self, key: str) -> str | None:
        self._purge()
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value
        if ex is not None:
            self._expiry[key] = time.time() + ex

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self._store.pop(k, None)
            self._expiry.pop(k, None)

    async def incr(self, key: str) -> int:
        self._purge()
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._store:
            self._expiry[key] = time.time() + seconds
            return True
        return False

    async def sadd(self, key: str, member: str) -> None:
        self._set_store.setdefault(key, set()).add(member)

    async def srem(self, key: str, member: str) -> None:
        self._set_store.get(key, set()).discard(member)

    async def sismember(self, key: str, member: str) -> bool:
        return member in self._set_store.get(key, set())

    async def smembers(self, key: str) -> set:
        return set(self._set_store.get(key, set()))

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self._store.clear()
        self._set_store.clear()
        self._expiry.clear()


async def init_redis():
    global _real_redis, _fallback
    try:
        from redis.asyncio import Redis as AsyncRedis

        _real_redis = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
        await _real_redis.ping()
    except Exception:
        _real_redis = None
        _fallback = _InMemoryRedis()
        print("⚠ Redis unavailable — using in-memory fallback")


async def close_redis():
    global _real_redis, _fallback
    if _real_redis:
        await _real_redis.aclose()
        _real_redis = None
    _fallback = None


def get_redis() -> _InMemoryRedis | AsyncRedis:
    if _real_redis is not None:
        return _real_redis
    if _fallback is not None:
        return _fallback
    raise RuntimeError("Redis not initialized. Call init_redis() first.")
