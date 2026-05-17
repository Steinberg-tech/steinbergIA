from datetime import datetime

from pydantic import BaseModel

from shared.constants import TicketStatus


class TicketCreate(BaseModel):
    session_id: str
    subject: str
    description: str
    order_id: str | None = None
    priority: str = "medium"


class TicketSchema(BaseModel):
    id: str
    protocol: str
    session_id: str
    subject: str
    status: TicketStatus
    priority: str
    created_at: datetime

    model_config = {"from_attributes": True}
