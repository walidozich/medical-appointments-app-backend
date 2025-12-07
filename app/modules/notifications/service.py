from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.notifications import repository, schemas
from datetime import datetime
from app.modules.chat import repository as chat_repo


def notify(db: Session, payload: schemas.NotificationCreate):
    return repository.create_notification(db, payload=payload.model_dump())


def list_my_notifications(
    db: Session,
    user_id: UUID,
    *,
    is_read: Optional[bool] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    return repository.list_notifications(
        db, user_id=user_id, is_read=is_read, type=type, skip=skip, limit=limit
    )


def list_since(db: Session, user_id: UUID, since: datetime, limit: int = 50):
    return repository.list_notifications_since(db, user_id=user_id, since=since, limit=limit)


def mark_notification_read(db: Session, notification_id: UUID, user_id: UUID):
    notif = repository.mark_read(db, notification_id=notification_id, user_id=user_id)
    if not notif:
        raise ValueError("Notification not found")
    return notif


def mark_all_notifications_read(db: Session, user_id: UUID) -> int:
    return repository.mark_all_read(db, user_id=user_id)


def delete_notification(db: Session, notification_id: UUID, user_id: UUID):
    ok = repository.delete_notification(db, notification_id=notification_id, user_id=user_id)
    if not ok:
        raise ValueError("Notification not found")
    return True


# Chat-specific helpers
def notify_message_sent(db: Session, *, thread_id: UUID, recipient_id: UUID, message_id: UUID):
    return notify(
        db,
        schemas.NotificationCreate(
            user_id=recipient_id,
            type="CHAT",
            title="New message",
            body=f"New message in thread {thread_id}",
        ),
    )


def notify_message_read(db: Session, *, thread_id: UUID, sender_id: UUID, message_id: UUID):
    return notify(
        db,
        schemas.NotificationCreate(
            user_id=sender_id,
            type="CHAT",
            title="Message read",
            body=f"Your message in thread {thread_id} was read",
        ),
    )


def notify_thread_created(db: Session, *, doctor_id: UUID, patient_id: UUID, thread_id: UUID, doctor_user_id: UUID, patient_user_id: UUID):
    notify(
        db,
        schemas.NotificationCreate(
            user_id=doctor_user_id,
            type="CHAT",
            title="New chat thread",
            body=f"Thread started with patient {patient_id}",
        ),
    )
    notify(
        db,
        schemas.NotificationCreate(
            user_id=patient_user_id,
            type="CHAT",
            title="New chat thread",
            body=f"Thread started with doctor {doctor_id}",
        ),
    )
