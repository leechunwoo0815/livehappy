from redis.asyncio import Redis as AsyncRedis

from app.config import settings

redis_client: AsyncRedis | None = None


async def init_redis():
    global redis_client
    redis_client = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
    await redis_client.ping()


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> AsyncRedis:
    assert redis_client is not None
    return redis_client
