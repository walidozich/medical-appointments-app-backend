from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.modules.appointments import service, schemas, repository as appt_repository
from app.modules.patients import repository as patients_repository
from app.modules.users.models import User

router = APIRouter()


@router.get("/me", response_model=List[schemas.AppointmentRead])
def list_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return service.list_patient_appointments(db, patient_id=patient.id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.AppointmentRead, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
):
    patient_id = payload.patient_id
    if not patient_id:
        patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
        patient_id = patient.id
    try:
        appt = service.create_appointment(db, patient_id=patient_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return appt


@router.post("/{appointment_id}/cancel", response_model=schemas.AppointmentRead)
def cancel_appointment(
    appointment_id: UUID,
    cancellation_reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
):
    # Ensure ownership for patient
    appt = appt_repository.get_by_id(db, appointment_id=appointment_id)
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if not current_user.is_superuser and getattr(current_user, "role_name", "").upper() == "PATIENT":
        patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
        if not patient or appt.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel this appointment")
    try:
        return service.cancel_appointment(db, appointment_id=appointment_id, cancellation_reason=cancellation_reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/doctor/me", response_model=List[schemas.AppointmentRead])
def list_my_doctor_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    from app.modules.doctors.repository import get_doctor_by_user

    doctor = get_doctor_by_user(db, user_id=current_user.id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return service.list_doctor_appointments(db, doctor_id=doctor.id, skip=skip, limit=limit)


@router.patch("/{appointment_id}/status", response_model=schemas.AppointmentRead)
def update_status(
    appointment_id: UUID,
    status_update: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    if not status_update.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status is required")
    try:
        appt = service.update_status(db, appointment_id=appointment_id, status=status_update.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return appt


@router.post("/{appointment_id}/reschedule", response_model=schemas.AppointmentRead)
def reschedule(
    appointment_id: UUID,
    payload: schemas.AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
):
    if not payload.start_time or not payload.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_time and end_time required")
    # Ensure ownership for patient
    appt = appt_repository.get_by_id(db, appointment_id=appointment_id)
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if getattr(current_user, "role_name", "").upper() == "PATIENT":
        patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
        if not patient or appt.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reschedule this appointment")
    try:
        return service.reschedule_appointment(db, appointment_id=appointment_id, start_time=payload.start_time, end_time=payload.end_time)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
