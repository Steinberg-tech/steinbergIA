from datetime import datetime

from pydantic import BaseModel, Field

from shared.constants import ConversationStatus, MessageRole, Platform


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., min_length=1, max_length=255)
    platform: Platform = Platform.API


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    session_id: str
    agent_used: str | None = None
    escalated: bool = False
    metadata: dict | None = None


class MessageSchema(BaseModel):
    id: str
    role: MessageRole
    content: str
    agent_used: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class ConversationSchema(BaseModel):
    id: str
    session_id: str
    platform: Platform
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema] = []

    model_config = {"from_attributes": True}
