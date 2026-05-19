from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    content: str
    is_read: bool
    related_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
