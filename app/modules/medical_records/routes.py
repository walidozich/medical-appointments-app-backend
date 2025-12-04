from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.modules.medical_records import service, schemas
from app.modules.users.models import User
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository

router = APIRouter()


@router.get("/me", response_model=List[schemas.MedicalRecordRead])
def list_my_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return service.list_for_patient(db, patient_id=patient.id, skip=skip, limit=limit)


@router.get("/doctor/me", response_model=List[schemas.MedicalRecordRead])
def list_my_patients_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    doctor = doctors_repository.get_doctor_by_user(db, user_id=current_user.id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return service.list_for_doctor(db, doctor_id=doctor.id, skip=skip, limit=limit)


@router.get("/{record_id}", response_model=schemas.MedicalRecordRead)
def get_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "PATIENT", "ADMIN")),
):
    try:
        rec = service.get_record(db, record_id=record_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    # ownership check: patient can only read own; doctor can read own patients
    role = getattr(current_user, "role_name", "").upper()
    if role == "PATIENT":
        patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
        if not patient or rec.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if role == "DOCTOR":
        doctor = doctors_repository.get_doctor_by_user(db, user_id=current_user.id)
        if not doctor or rec.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return rec


@router.post("/", response_model=schemas.MedicalRecordRead, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: schemas.MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    doctor_id = None
    role = getattr(current_user, "role_name", "").upper()
    if role == "DOCTOR":
        doctor = doctors_repository.get_doctor_by_user(db, user_id=current_user.id)
        if not doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
        doctor_id = doctor.id
    try:
        rec = service.create_record(db, payload=payload, patient_id=payload.patient_id, doctor_id=doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return rec


@router.patch("/{record_id}", response_model=schemas.MedicalRecordRead)
def update_record(
    record_id: UUID,
    payload: schemas.MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    try:
        rec = service.update_record(db, record_id=record_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return rec


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    try:
        service.delete_record(db, record_id=record_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
