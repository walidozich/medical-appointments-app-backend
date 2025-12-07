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


def list_messages(db: Session, thread_id: UUID, skip: int = 0, limit: int = 50) -> List[models.ChatMessage]:
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.thread_id == thread_id)
        .order_by(models.ChatMessage.sent_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def add_message(db: Session, *, thread_id: UUID, sender_id: UUID, sender_role: str, content: str) -> models.ChatMessage:
    msg = models.ChatMessage(thread_id=thread_id, sender_id=sender_id, sender_role=sender_role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
