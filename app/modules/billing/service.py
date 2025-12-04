from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.billing import repository, schemas
from app.modules.patients import repository as patients_repository
from app.modules.appointments import repository as appointments_repository

VALID_BILLING_STATUS = {"PENDING", "PAID", "VOID", "REFUNDED"}
VALID_CLAIM_STATUS = {"PENDING", "SUBMITTED", "APPROVED", "REJECTED", "PAID"}


def _ensure_patient(db: Session, patient_id: UUID):
    patient = patients_repository.get_by_id(db, patient_id)
    if not patient:
        raise ValueError("Patient not found")
    return patient


def create_billing(db: Session, payload: schemas.BillingCreate):
    data = payload.model_dump(exclude_unset=True)
    pid = data.get("patient_id")
    if pid:
        _ensure_patient(db, pid)
    appt_id = data.get("appointment_id")
    if appt_id:
        appt = appointments_repository.get_by_id(db, appointment_id=appt_id)
        if not appt:
            raise ValueError("Appointment not found")
        data.setdefault("patient_id", appt.patient_id)
    return repository.create_billing(db, data)


def update_billing(db: Session, billing_id: UUID, payload: schemas.BillingUpdate):
    bill = repository.get_billing(db, billing_id)
    if not bill:
        raise ValueError("Billing not found")
    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] and updates["status"] not in VALID_BILLING_STATUS:
        raise ValueError("Invalid status")
    return repository.update_billing(db, billing=bill, updates=updates)


def list_billing_for_patient(db: Session, patient_id: UUID, skip=0, limit=100):
    _ensure_patient(db, patient_id)
    return repository.list_billing_for_patient(db, patient_id=patient_id, skip=skip, limit=limit)


def get_billing(db: Session, billing_id: UUID):
    bill = repository.get_billing(db, billing_id)
    if not bill:
        raise ValueError("Billing not found")
    return bill


def create_policy(db: Session, payload: schemas.InsurancePolicyCreate):
    data = payload.model_dump(exclude_unset=True)
    pid = data.get("patient_id")
    if not pid:
        raise ValueError("patient_id is required")
    _ensure_patient(db, pid)
    return repository.create_policy(db, data)


def update_policy(db: Session, policy_id: UUID, payload: schemas.InsurancePolicyUpdate):
    policy = repository.get_policy(db, policy_id)
    if not policy:
        raise ValueError("Insurance policy not found")
    updates = payload.model_dump(exclude_unset=True)
    return repository.update_policy(db, policy=policy, updates=updates)


def delete_policy(db: Session, policy_id: UUID):
    policy = repository.get_policy(db, policy_id)
    if not policy:
        raise ValueError("Insurance policy not found")
    repository.delete_policy(db, policy)
    return True


def list_policies_for_patient(db: Session, patient_id: UUID, skip=0, limit=100):
    _ensure_patient(db, patient_id)
    return repository.list_policies_for_patient(db, patient_id=patient_id, skip=skip, limit=limit)


def create_claim(db: Session, payload: schemas.InsuranceClaimCreate):
    data = payload.model_dump(exclude_unset=True)
    policy = repository.get_policy(db, data["policy_id"])
    if not policy:
        raise ValueError("Insurance policy not found")
    if "billing_id" in data and data["billing_id"]:
        bill = repository.get_billing(db, data["billing_id"])
        if not bill:
            raise ValueError("Billing not found")
    return repository.create_claim(db, data)


def update_claim(db: Session, claim_id: UUID, payload: schemas.InsuranceClaimUpdate):
    claim = repository.get_claim(db, claim_id)
    if not claim:
        raise ValueError("Insurance claim not found")
    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] and updates["status"] not in VALID_CLAIM_STATUS:
        raise ValueError("Invalid claim status")
    return repository.update_claim(db, claim=claim, updates=updates)


def list_claims_for_policy(db: Session, policy_id: UUID, skip=0, limit=100):
    policy = repository.get_policy(db, policy_id)
    if not policy:
        raise ValueError("Insurance policy not found")
    return repository.list_claims_for_policy(db, policy_id=policy_id, skip=skip, limit=limit)
