from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class ChatThreadCreate(BaseModel):
    doctor_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None


class ChatThreadRead(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: Optional[str] = Field(default=None, max_length=2000)


class ChatMessageRead(BaseModel):
    id: UUID
    thread_id: UUID
    sender_id: UUID
    sender_role: str
    content: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    sent_at: datetime
    read_at: Optional[datetime] = None
    is_system_message: bool

    model_config = {"from_attributes": True}


class ChatThreadWithMessages(ChatThreadRead):
    messages: List[ChatMessageRead] = []


class ChatAttachmentUpload(BaseModel):
    caption: Optional[str] = None
