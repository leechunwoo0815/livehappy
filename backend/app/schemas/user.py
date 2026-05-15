from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    avatar: str | None = None
    role: str
    bio: str | None = None
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}
