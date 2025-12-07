from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.modules.notifications import service, schemas
from app.modules.users.models import User


router = APIRouter()


@router.get("/", response_model=List[schemas.NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    is_read: Optional[bool] = None,
    type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    return service.list_my_notifications(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_read=is_read,
        type=type,
    )


@router.post("/", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if payload.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create for other users")
    return service.notify(db, payload)


@router.patch("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return service.mark_notification_read(db, notification_id=notification_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/read-all", response_model=int)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return service.mark_all_notifications_read(db, user_id=current_user.id)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        service.delete_notification(db, notification_id=notification_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
