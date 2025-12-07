from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.chat import models


def get_thread(db: Session, thread_id: UUID) -> Optional[models.ChatThread]:
    return db.query(models.ChatThread).filter(models.ChatThread.id == thread_id).first()


def get_thread_by_participants(db: Session, patient_id: UUID, doctor_id: UUID) -> Optional[models.ChatThread]:
    return (
        db.query(models.ChatThread)
        .filter(models.ChatThread.patient_id == patient_id, models.ChatThread.doctor_id == doctor_id)
        .first()
    )


def list_threads_for_patient(db: Session, patient_id: UUID) -> List[models.ChatThread]:
    return db.query(models.ChatThread).filter(models.ChatThread.patient_id == patient_id).all()


def list_threads_for_doctor(db: Session, doctor_id: UUID) -> List[models.ChatThread]:
    return db.query(models.ChatThread).filter(models.ChatThread.doctor_id == doctor_id).all()


def create_thread(db: Session, *, patient_id: UUID, doctor_id: UUID) -> models.ChatThread:
    thread = models.ChatThread(patient_id=patient_id, doctor_id=doctor_id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def update_thread_status(db: Session, thread: models.ChatThread, status: str) -> models.ChatThread:
    thread.status = status
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def list_messages(db: Session, thread_id: UUID, skip: int = 0, limit: int = 50) -> List[models.ChatMessage]:
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.thread_id == thread_id)
        .order_by(models.ChatMessage.sent_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def add_message(
    db: Session,
    *,
    thread_id: UUID,
    sender_id: UUID,
    sender_role: str,
    content: str | None = None,
    file_url: str | None = None,
    file_type: str | None = None,
) -> models.ChatMessage:
    msg = models.ChatMessage(
        thread_id=thread_id,
        sender_id=sender_id,
        sender_role=sender_role,
        content=content,
        file_url=file_url,
        file_type=file_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_message(db: Session, message_id: UUID) -> Optional[models.ChatMessage]:
    return db.query(models.ChatMessage).filter(models.ChatMessage.id == message_id).first()


def mark_message_read(db: Session, message: models.ChatMessage) -> models.ChatMessage:
    from datetime import datetime, timezone

    if not message.read_at:
        message.read_at = datetime.now(timezone.utc)
        db.add(message)
        db.commit()
        db.refresh(message)
    return message


def get_or_create_pref(db: Session, user_id: UUID, thread_id: UUID) -> models.ChatThreadPreference:
    pref = (
        db.query(models.ChatThreadPreference)
        .filter(models.ChatThreadPreference.user_id == user_id, models.ChatThreadPreference.thread_id == thread_id)
        .first()
    )
    if pref:
        return pref
    pref = models.ChatThreadPreference(user_id=user_id, thread_id=thread_id, is_archived=False)
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def set_archived(db: Session, user_id: UUID, thread_id: UUID, is_archived: bool) -> models.ChatThreadPreference:
    pref = get_or_create_pref(db, user_id=user_id, thread_id=thread_id)
    pref.is_archived = is_archived
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref
