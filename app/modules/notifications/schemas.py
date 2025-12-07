from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: UUID
    type: str
    title: str
    body: Optional[str] = None


class NotificationRead(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    body: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
