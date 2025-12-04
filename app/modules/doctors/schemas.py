from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class SpecialtyBase(BaseModel):
    name: str
    description: Optional[str] = None


class SpecialtyRead(SpecialtyBase):
    id: int

    model_config = {"from_attributes": True}


class DoctorAvailabilityBase(BaseModel):
    weekday: str
    start_time: time
    end_time: time
    is_active: bool = True


class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    pass


class DoctorAvailabilityUpdate(BaseModel):
    weekday: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class DoctorAvailabilityRead(DoctorAvailabilityBase):
    id: UUID
    doctor_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DoctorBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    years_experience: Optional[int] = None
    clinic_address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    specialties: Optional[List[str]] = None


class DoctorCreate(DoctorBase):
    user_id: Optional[UUID] = None


class DoctorUpdate(DoctorBase):
    specialties: Optional[List[str]] = None


class DoctorRead(DoctorBase):
    id: UUID
    user_id: UUID
    avg_rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime
    specialties: List[SpecialtyRead] = []

    model_config = {"from_attributes": True}
