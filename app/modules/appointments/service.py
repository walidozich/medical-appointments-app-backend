from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.appointments import repository, schemas
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository
from app.modules.doctors import models as doctor_models
from app.modules.notifications import service as notifications_service, schemas as notif_schemas


VALID_STATUSES = {"SCHEDULED", "COMPLETED", "CANCELLED"}


def _validate_times(start_time: datetime, end_time: datetime):
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")


def _check_doctor_availability(db: Session, doctor_id: UUID, start_time: datetime, end_time: datetime):
    weekday = start_time.strftime("%a")
    availabilities = (
        db.query(doctor_models.DoctorAvailability)
        .filter(
            doctor_models.DoctorAvailability.doctor_id == doctor_id,
            doctor_models.DoctorAvailability.is_active.is_(True),
            doctor_models.DoctorAvailability.weekday == weekday,
        )
        .all()
    )
    if availabilities:
        # If availability records exist, ensure the requested window fits at least one slot
        start_t = start_time.time()
        end_t = end_time.time()
        fits = any(a.start_time <= start_t and a.end_time >= end_t for a in availabilities)
        if not fits:
            raise ValueError("Requested time is outside doctor's availability")


def list_patient_appointments(db: Session, patient_id: UUID, skip: int = 0, limit: int = 100):
    return repository.list_appointments_for_patient(db, patient_id=patient_id, skip=skip, limit=limit)


def list_doctor_appointments(db: Session, doctor_id: UUID, skip: int = 0, limit: int = 100):
    return repository.list_appointments_for_doctor(db, doctor_id=doctor_id, skip=skip, limit=limit)


def create_appointment(db: Session, patient_id: UUID | None, payload: schemas.AppointmentCreate):
    pid = patient_id or payload.patient_id
    if not pid:
        raise ValueError("patient_id is required")
    patient = patients_repository.get_by_id(db, pid)
    if not patient:
        raise ValueError("Patient not found")
    doctor = doctors_repository.get_doctor(db, doctor_id=payload.doctor_id)
    if not doctor:
        raise ValueError("Doctor not found")

    _validate_times(payload.start_time, payload.end_time)
    _check_doctor_availability(db, doctor_id=doctor.id, start_time=payload.start_time, end_time=payload.end_time)

    if repository.has_conflict(db, doctor_id=doctor.id, start_time=payload.start_time, end_time=payload.end_time):
        raise ValueError("Doctor is not available at the requested time")

    return repository.create_appointment(
        db,
        {
            **payload.model_dump(exclude_unset=True),
            "patient_id": patient.id,
            "status": "SCHEDULED",
        },
    )
    notifications_service.notify(
        db,
        notif_schemas.NotificationCreate(
            user_id=doctor.user_id,
            type="APPOINTMENT",
            title="New appointment booked",
            body=f"Patient booked for {payload.start_time.isoformat()}",
        ),
    )
    notifications_service.notify(
        db,
        notif_schemas.NotificationCreate(
            user_id=patient.user_id,
            type="APPOINTMENT",
            title="Appointment confirmed",
            body=f"With Dr. {doctor.last_name or doctor.first_name} at {payload.start_time.isoformat()}",
        ),
    )


def cancel_appointment(db: Session, appointment_id: UUID, cancellation_reason: str | None = None):
    appt = repository.get_by_id(db, appointment_id=appointment_id)
    if not appt:
        raise ValueError("Appointment not found")
    if appt.status == "CANCELLED":
        return appt
    updates = {"status": "CANCELLED", "cancellation_reason": cancellation_reason}
    updated = repository.update_appointment(db, appointment=appt, updates=updates)
    patient = appt.patient
    doctor = appt.doctor
    if patient and getattr(patient, "user_id", None):
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=patient.user_id,
                type="APPOINTMENT",
                title="Appointment cancelled",
                body=cancellation_reason or "Your appointment was cancelled",
            ),
        )
    if doctor and getattr(doctor, "user_id", None):
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=doctor.user_id,
                type="APPOINTMENT",
                title="Appointment cancelled",
                body="Patient cancelled an appointment.",
            ),
        )
    return updated


def update_status(db: Session, appointment_id: UUID, status: str):
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status")
    appt = repository.get_by_id(db, appointment_id=appointment_id)
    if not appt:
        raise ValueError("Appointment not found")
    updated = repository.update_appointment(db, appointment=appt, updates={"status": status})
    patient = appt.patient
    doctor = appt.doctor
    if patient and getattr(patient, "user_id", None):
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=patient.user_id,
                type="APPOINTMENT",
                title=f"Appointment {status.title()}",
                body="Status changed.",
            ),
        )
    if doctor and getattr(doctor, "user_id", None):
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=doctor.user_id,
                type="APPOINTMENT",
                title=f"Appointment {status.title()}",
                body="Status changed.",
            ),
        )
    return updated


def reschedule_appointment(db: Session, appointment_id: UUID, start_time: datetime, end_time: datetime):
    appt = repository.get_by_id(db, appointment_id=appointment_id)
    if not appt:
        raise ValueError("Appointment not found")
    _validate_times(start_time, end_time)
    _check_doctor_availability(db, doctor_id=appt.doctor_id, start_time=start_time, end_time=end_time)
    if repository.has_conflict(db, doctor_id=appt.doctor_id, start_time=start_time, end_time=end_time):
        raise ValueError("Doctor is not available at the requested time")
    updated = repository.update_appointment(
        db,
        appointment=appt,
        updates={"start_time": start_time, "end_time": end_time, "status": "SCHEDULED"},
    )
    patient = appt.patient
    doctor = appt.doctor
    if patient and getattr(patient, "user_id", None):
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=patient.user_id,
                type="APPOINTMENT",
                title="Appointment rescheduled",
                body=f"New time: {start_time.isoformat()}",
            ),
        )
    if doctor and getattr(doctor, "user_id", None):
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=doctor.user_id,
                type="APPOINTMENT",
                title="Appointment rescheduled",
                body=f"New time: {start_time.isoformat()}",
            ),
        )
    return updated
