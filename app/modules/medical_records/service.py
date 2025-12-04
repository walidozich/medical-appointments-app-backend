from sqlalchemy.orm import Session
from uuid import UUID

from app.modules.medical_records import repository, schemas
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository


def list_for_patient(db: Session, patient_id: UUID, skip: int = 0, limit: int = 100):
    return repository.list_by_patient(db, patient_id=patient_id, skip=skip, limit=limit)


def list_for_doctor(db: Session, doctor_id: UUID, skip: int = 0, limit: int = 100):
    return repository.list_by_doctor(db, doctor_id=doctor_id, skip=skip, limit=limit)


def get_record(db: Session, record_id: UUID):
    rec = repository.get_by_id(db, record_id=record_id)
    if not rec:
        raise ValueError("Medical record not found")
    return rec


def create_record(db: Session, payload: schemas.MedicalRecordCreate, patient_id: UUID | None, doctor_id: UUID | None):
    pid = patient_id or payload.patient_id
    did = doctor_id or payload.doctor_id
    if not pid:
        raise ValueError("patient_id is required")
    if not did:
        raise ValueError("doctor_id is required")
    patient = patients_repository.get_by_id(db, pid)
    if not patient:
        raise ValueError("Patient not found")
    doctor = doctors_repository.get_doctor(db, did)
    if not doctor:
        raise ValueError("Doctor not found")

    data = payload.model_dump(exclude_unset=True)
    data["patient_id"] = patient.id
    data["doctor_id"] = doctor.id
    return repository.create_record(db, data)


def update_record(db: Session, record_id: UUID, payload: schemas.MedicalRecordUpdate):
    rec = get_record(db, record_id)
    updates = payload.model_dump(exclude_unset=True)
    return repository.update_record(db, record=rec, updates=updates)


def delete_record(db: Session, record_id: UUID):
    rec = get_record(db, record_id)
    repository.delete_record(db, record=rec)
    return True
