from uuid import UUID
from typing import List

from sqlalchemy.orm import Session

from app.modules.chat import repository, schemas
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository
from app.modules.notifications import service as notifications_service, schemas as notif_schemas


def _get_patient(db: Session, user_id: UUID):
    patient = patients_repository.get_by_user_id(db, user_id)
    if not patient:
        raise ValueError("Patient profile not found")
    return patient


def _get_doctor(db: Session, user_id: UUID):
    doctor = doctors_repository.get_doctor_by_user(db, user_id=user_id)
    if not doctor:
        raise ValueError("Doctor profile not found")
    return doctor


def get_or_create_thread(db: Session, current_user, payload: schemas.ChatThreadCreate):
    role = getattr(current_user, "role_name", "").upper()
    patient = None
    doctor = None
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        doctor_id = payload.doctor_id
        if not doctor_id:
            raise ValueError("doctor_id is required for patients")
        doctor = doctors_repository.get_doctor(db, doctor_id=doctor_id)
    elif role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        patient_id = payload.patient_id
        if not patient_id:
            raise ValueError("patient_id is required for doctors")
        patient = patients_repository.get_by_id(db, patient_id)
    else:
        raise ValueError("Only patients or doctors can start threads")

    if not patient or not doctor:
        raise ValueError("Participant not found")

    patient_id = patient.id
    doctor_id = doctor.id

    existing = repository.get_thread_by_participants(db, patient_id=patient_id, doctor_id=doctor_id)
    if existing:
        return existing
    return repository.create_thread(db, patient_id=patient_id, doctor_id=doctor_id)


def list_threads(db: Session, current_user) -> List:
    role = getattr(current_user, "role_name", "").upper()
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        return repository.list_threads_for_patient(db, patient_id=patient.id)
    if role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        return repository.list_threads_for_doctor(db, doctor_id=doctor.id)
    return []


def list_messages(db: Session, current_user, thread_id: UUID, skip: int = 0, limit: int = 50):
    thread = repository.get_thread(db, thread_id=thread_id)
    if not thread:
        raise ValueError("Thread not found")
    role = getattr(current_user, "role_name", "").upper()
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        if thread.patient_id != patient.id:
            raise ValueError("Not a participant in this thread")
    elif role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        if thread.doctor_id != doctor.id:
            raise ValueError("Not a participant in this thread")
    else:
        raise ValueError("Not allowed")
    return repository.list_messages(db, thread_id=thread.id, skip=skip, limit=limit)


def post_message(db: Session, current_user, thread_id: UUID, msg_in: schemas.ChatMessageCreate):
    thread = repository.get_thread(db, thread_id=thread_id)
    if not thread:
        raise ValueError("Thread not found")
    role = getattr(current_user, "role_name", "").upper()
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        if thread.patient_id != patient.id:
            raise ValueError("Not a participant in this thread")
        sender_role = "PATIENT"
        recipient_user_id = getattr(thread.doctor, "user_id", None) if hasattr(thread, "doctor") else None
    elif role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        if thread.doctor_id != doctor.id:
            raise ValueError("Not a participant in this thread")
        sender_role = "DOCTOR"
        recipient_user_id = getattr(thread, "patient", None).user_id if getattr(thread, "patient", None) else None
    else:
        raise ValueError("Not allowed")
    message = repository.add_message(
        db,
        thread_id=thread.id,
        sender_id=current_user.id,
        sender_role=sender_role,
        content=msg_in.content,
    )
    if recipient_user_id:
        notifications_service.notify(
            db,
            notif_schemas.NotificationCreate(
                user_id=recipient_user_id,
                type="CHAT",
                title="New message",
                body=msg_in.content[:200],
            ),
        )
    return message
