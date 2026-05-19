from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.handlers import register_exception_handlers
from app.database import engine
from app.middleware.auth import JWTMiddleware
from app.middleware.ratelimit import RateLimitMiddleware
from app.models import Base
from app.redis import close_redis, init_redis
from app.routers import (
    admin,
    ai,
    auth,
    bookings,
    health,
    listings,
    messages,
    notifications,
    reviews,
    social,
    upload,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    await init_redis()
    yield
    await close_redis()
    await engine.dispose()


if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

app.include_router(health.router, tags=["健康"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(listings.router, prefix="/api/listings", tags=["房源"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["预订"])
app.include_router(messages.router, prefix="/api/messages", tags=["消息"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知"])
app.include_router(social.router, prefix="/api/social", tags=["社交"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["评价"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(upload.router, prefix="/api", tags=["上传"])
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/info")
async def api_info():
    return {"name": settings.app_name, "version": settings.app_version, "status": "ok"}

# 前端静态文件挂载（必须在所有 API 路由之后）
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
