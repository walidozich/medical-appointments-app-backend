from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class BillingBase(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "USD"
    description: Optional[str] = None
    appointment_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None


class BillingCreate(BillingBase):
    pass


class BillingUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    currency: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class BillingRead(BillingBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InsurancePolicyBase(BaseModel):
    provider_name: str
    policy_number: str
    coverage_details: Optional[str] = None
    patient_id: Optional[UUID] = None


class InsurancePolicyCreate(InsurancePolicyBase):
    pass


class InsurancePolicyUpdate(BaseModel):
    provider_name: Optional[str] = None
    policy_number: Optional[str] = None
    coverage_details: Optional[str] = None


class InsurancePolicyRead(InsurancePolicyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InsuranceClaimBase(BaseModel):
    policy_id: UUID
    billing_id: Optional[UUID] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InsuranceClaimCreate(InsuranceClaimBase):
    pass


class InsuranceClaimUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class InsuranceClaimRead(InsuranceClaimBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
