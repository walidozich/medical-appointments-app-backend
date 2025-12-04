from sqlalchemy.orm import Session
from uuid import UUID

from app.modules.patients import repository, models, schemas
from app.modules.users import repository as users_repository


def _ensure_user_is_patient(db: Session, user_id: UUID):
    user = users_repository.get_by_id(db, user_id=user_id)
    if not user:
        raise ValueError("User not found")
    role_name = getattr(user, "role_name", None)
    if not role_name or role_name.upper() != "PATIENT":
        raise ValueError("User is not a patient")
    return user


def list_patients(db: Session, skip: int = 0, limit: int = 100):
    return repository.list_patients(db, skip=skip, limit=limit)


def get_patient(db: Session, patient_id: UUID):
    patient = repository.get_by_id(db, patient_id=patient_id)
    if not patient:
        raise ValueError("Patient not found")
    return patient


def get_patient_by_user(db: Session, user_id: UUID):
    patient = repository.get_by_user_id(db, user_id=user_id)
    if not patient:
        raise ValueError("Patient not found")
    return patient


def create_patient(db: Session, user_id: UUID, patient_in: schemas.PatientCreate):
    _ensure_user_is_patient(db, user_id)
    existing = repository.get_by_user_id(db, user_id=user_id)
    if existing:
        raise ValueError("Patient profile already exists")
    payload = patient_in.model_dump(exclude_unset=True)
    payload["user_id"] = user_id
    return repository.create_patient(db, payload)


def update_patient(db: Session, patient_id: UUID, patient_in: schemas.PatientUpdate):
    patient = get_patient(db, patient_id)
    updates = patient_in.model_dump(exclude_unset=True)
    return repository.update_patient(db, patient=patient, updates=updates)


def update_patient_for_user(db: Session, user_id: UUID, patient_in: schemas.PatientUpdate):
    patient = repository.get_by_user_id(db, user_id=user_id)
    if not patient:
        raise ValueError("Patient not found")
    updates = patient_in.model_dump(exclude_unset=True)
    return repository.update_patient(db, patient=patient, updates=updates)


def delete_patient(db: Session, patient_id: UUID):
    patient = get_patient(db, patient_id)
    repository.delete_patient(db, patient=patient)
    return True
