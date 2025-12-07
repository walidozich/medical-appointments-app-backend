from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.notifications import models


def create_notification(db: Session, payload: dict) -> models.Notification:
    notif = models.Notification(**payload)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def list_notifications(
    db: Session,
    user_id: UUID,
    *,
    is_read: Optional[bool] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[models.Notification]:
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if is_read is not None:
        query = query.filter(models.Notification.is_read.is_(is_read))
    if type:
        query = query.filter(models.Notification.type == type)
    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_read(db: Session, notification_id: UUID, user_id: UUID) -> models.Notification | None:
    notif = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id, models.Notification.user_id == user_id)
        .first()
    )
    if not notif:
        return None
    notif.is_read = True
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_read(db: Session, user_id: UUID) -> int:
    updated = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id, models.Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return updated


def delete_notification(db: Session, notification_id: UUID, user_id: UUID) -> bool:
    notif = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id, models.Notification.user_id == user_id)
        .first()
    )
    if not notif:
        return False
    db.delete(notif)
    db.commit()
    return True
