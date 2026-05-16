from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.elasticsearch import close_elasticsearch, init_elasticsearch
from app.kafka import close_kafka, init_kafka
from app.models import Base
from app.redis import close_redis, init_redis
from app.routers import ai, auth, bookings, listings, messages, reviews, social, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    await init_kafka()
    await init_elasticsearch()
    yield
    await close_elasticsearch()
    await close_kafka()
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(listings.router, prefix="/api/listings", tags=["房源"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["预订"])
app.include_router(messages.router, prefix="/api/messages", tags=["消息"])
app.include_router(social.router, prefix="/api/social", tags=["社交"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["评价"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version, "status": "ok"}
