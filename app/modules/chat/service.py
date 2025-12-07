from uuid import UUID
from typing import List

from sqlalchemy.orm import Session

from app.modules.chat import repository, schemas
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository
from app.modules.notifications import service as notifications_service, schemas as notif_schemas
from app.modules.chat import models as chat_models
from app.utils.storage import LocalStorage
from fastapi import UploadFile
from typing import Optional


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
    thread = repository.create_thread(db, patient_id=patient_id, doctor_id=doctor_id)
    # Notify both participants
    notifications_service.notify_thread_created(
        db,
        doctor_id=doctor_id,
        patient_id=patient_id,
        thread_id=thread.id,
        doctor_user_id=doctor.user_id,
        patient_user_id=patient.user_id,
    )
    return thread


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
    if thread.status.lower() == "closed":
        raise ValueError("Thread is closed")
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
        notifications_service.notify_message_sent(
            db,
            thread_id=thread.id,
            recipient_id=recipient_user_id,
            message_id=message.id,
        )
    return message


def mark_message_read(db: Session, current_user, message_id: UUID, on_broadcast: callable | None = None):
    msg = repository.get_message(db, message_id=message_id)
    if not msg:
        raise ValueError("Message not found")
    thread = repository.get_thread(db, thread_id=msg.thread_id)
    if not thread:
        raise ValueError("Thread not found")

    role = getattr(current_user, "role_name", "").upper()
    recipient_user_id = None
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        if thread.patient_id != patient.id:
            raise ValueError("Not a participant")
        recipient_user_id = getattr(thread.doctor, "user_id", None) if hasattr(thread, "doctor") else None
    elif role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        if thread.doctor_id != doctor.id:
            raise ValueError("Not a participant")
        recipient_user_id = getattr(thread.patient, "user_id", None) if hasattr(thread, "patient") else None
    else:
        raise ValueError("Not allowed")

    # only recipient can mark read
    if msg.sender_id == current_user.id:
        raise ValueError("Sender cannot mark their own message as read")
    msg = repository.mark_message_read(db, msg)

    if on_broadcast:
        try:
            on_broadcast(msg)
        except Exception:
            # don't fail the API on broadcast issues
            pass
    # notify sender their message was read
    notifications_service.notify_message_read(
        db,
        thread_id=msg.thread_id,
        sender_id=msg.sender_id,
        message_id=msg.id,
    )
    return msg


def update_thread_status(db: Session, current_user, thread_id: UUID, status: str):
    status = status.lower()
    if status not in {"open", "closed", "archived"}:
        raise ValueError("Invalid status")
    thread = repository.get_thread(db, thread_id=thread_id)
    if not thread:
        raise ValueError("Thread not found")

    role = getattr(current_user, "role_name", "").upper()
    # ensure participant
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        if thread.patient_id != patient.id:
            raise ValueError("Not a participant")
    elif role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        if thread.doctor_id != doctor.id:
            raise ValueError("Not a participant")
    else:
        raise ValueError("Not allowed")

    if status == "archived":
        repository.set_archived(db, user_id=current_user.id, thread_id=thread.id, is_archived=True)
        return thread  # status remains unchanged globally

    # open/closed is global
    thread = repository.update_thread_status(db, thread=thread, status=status)
    return thread


ALLOWED_FILE_TYPES = {"image/png", "image/jpeg", "image/jpg", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def upload_attachment(
    db: Session,
    current_user,
    thread_id: UUID,
    file: UploadFile,
    caption: Optional[str] = None,
    storage: Optional[LocalStorage] = None,
):
    storage = storage or LocalStorage()
    thread = repository.get_thread(db, thread_id=thread_id)
    if not thread:
        raise ValueError("Thread not found")
    if thread.status.lower() == "closed":
        raise ValueError("Thread is closed")

    role = getattr(current_user, "role_name", "").upper()
    if role == "PATIENT":
        patient = _get_patient(db, current_user.id)
        if thread.patient_id != patient.id:
            raise ValueError("Not a participant")
        sender_role = "PATIENT"
        recipient_user_id = getattr(thread.doctor, "user_id", None) if getattr(thread, "doctor", None) else None
    elif role == "DOCTOR":
        doctor = _get_doctor(db, current_user.id)
        if thread.doctor_id != doctor.id:
            raise ValueError("Not a participant")
        sender_role = "DOCTOR"
        recipient_user_id = getattr(thread.patient, "user_id", None) if getattr(thread, "patient", None) else None
    else:
        raise ValueError("Not allowed")

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise ValueError("Unsupported file type")
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError("File too large")

    file_url = storage.save(file.file, file.filename or "upload.bin")
    msg = repository.add_message(
        db,
        thread_id=thread.id,
        sender_id=current_user.id,
        sender_role=sender_role,
        content=caption,
        file_url=file_url,
        file_type=file.content_type,
    )

    if recipient_user_id:
        notifications_service.notify_message_sent(
            db,
            thread_id=thread.id,
            recipient_id=recipient_user_id,
            message_id=msg.id,
        )

    return msg
