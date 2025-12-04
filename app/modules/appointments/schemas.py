from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AppointmentBase(BaseModel):
    doctor_id: UUID
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    patient_id: Optional[UUID] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    cancellation_reason: Optional[str] = None


class AppointmentRead(AppointmentBase):
    id: UUID
    patient_id: UUID
    status: str
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
