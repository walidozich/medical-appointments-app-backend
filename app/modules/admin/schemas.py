from typing import Dict
from pydantic import BaseModel


class UsersSummary(BaseModel):
    total: int
    active: int
    by_role: Dict[str, int]


class ProfilesSummary(BaseModel):
    patients: int
    doctors: int


class AppointmentsSummary(BaseModel):
    total: int
    by_status: Dict[str, int]


class BillingSummary(BaseModel):
    paid_total: float
    pending_total: float


class Summary(BaseModel):
    users: UsersSummary
    profiles: ProfilesSummary
    appointments: AppointmentsSummary
    billing: BillingSummary
