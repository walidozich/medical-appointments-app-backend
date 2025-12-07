from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.notifications import repository, schemas


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
