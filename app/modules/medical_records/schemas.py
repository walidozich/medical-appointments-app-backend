from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MedicalRecordBase(BaseModel):
    diagnosis: str
    treatment_plan: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordCreate(MedicalRecordBase):
    patient_id: Optional[UUID] = None
    doctor_id: Optional[UUID] = None


class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordRead(MedicalRecordBase):
    id: UUID
    patient_id: UUID
    doctor_id: Optional[UUID] = None
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
