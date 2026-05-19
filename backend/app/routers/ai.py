from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.common import BaseResponse
from app.services.ai import chat as ai_chat

router = APIRouter()


@router.post("/chat", response_model=BaseResponse)
async def chat(
    content: str = Body(..., embed=True),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await ai_chat(db, user_id, content)
    return BaseResponse(success=True, data=result)
