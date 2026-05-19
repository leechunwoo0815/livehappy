from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine
from app.redis import get_redis
from app.schemas.common import BaseResponse

router = APIRouter()


@router.get("/health", response_model=BaseResponse)
async def health():
    status = {"status": "ok", "services": {}}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["services"]["database"] = "ok"
    except Exception as e:
        status["services"]["database"] = f"error: {e}"
        status["status"] = "degraded"

    try:
        redis = get_redis()
        await redis.ping()
        status["services"]["redis"] = "ok"
    except Exception as e:
        status["services"]["redis"] = f"error: {e}"
        status["status"] = "degraded"

    return BaseResponse(success=True, data=status)
