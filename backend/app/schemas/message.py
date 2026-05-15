from datetime import datetime

from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    receiver_id: str
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    participant_one: str
    participant_two: str
    last_message: str | None
    unread_count_one: int
    unread_count_two: int
    created_at: datetime

    model_config = {"from_attributes": True}
