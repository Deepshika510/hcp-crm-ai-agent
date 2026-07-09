from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InteractionCreate(BaseModel):
    hcp_id: int
    channel: str
    products_discussed: str
    summary: str
    sentiment: Optional[str] = None
    follow_up_action: Optional[str] = None
    raw_input: Optional[str] = None

class InteractionResponse(InteractionCreate):
    id: int
    interaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True