import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitException
from app.redis import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        if request.method in ("GET", "OPTIONS") or "/uploads/" in request.url.path:
            return await call_next(request)

        try:
            r = get_redis()
            client_ip = request.client.host if request.client else "unknown"
            key = f"ratelimit:{client_ip}:{int(time.time() / self.window_seconds)}"
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, self.window_seconds)
            if count > self.max_requests:
                raise RateLimitException()
        except RuntimeError:
            pass
        return await call_next(request)
