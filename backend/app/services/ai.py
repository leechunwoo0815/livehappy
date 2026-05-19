import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chat import ChatMessage

MOCK_REPLIES = [
    "您好！我是 StayHub 智能助手，很高兴为您服务。",
    "请问有什么可以帮助您的吗？",
    "我理解您的问题，让我为您查询相关信息。",
    "好的，已为您记录，稍后会有专人与您联系。",
    "根据您的需求，我推荐您查看北京地区的精品房源。",
    "关于退款政策，我们支持入住前24小时免费取消。",
    "您的预订已确认，祝您入住愉快！",
]


async def chat(db: AsyncSession, user_id: str, content: str) -> dict:
    msg = ChatMessage(user_id=user_id, content=content, role="user")
    db.add(msg)
    await db.commit()

    if settings.deepseek_api_key and settings.ai_enabled:
        reply_content = await _call_deepseek(content)
    else:
        reply_content = random.choice(MOCK_REPLIES)

    reply = ChatMessage(user_id=user_id, content=reply_content, role="assistant")
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return {"reply": reply.content, "role": reply.role}


async def _call_deepseek(prompt: str) -> str:
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.deepseek_api_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return random.choice(MOCK_REPLIES)
