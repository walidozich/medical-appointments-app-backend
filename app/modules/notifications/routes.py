from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import asyncio

from app.core.dependencies import get_db, get_current_active_user
from app.modules.notifications import service, schemas
from app.modules.users.models import User
from app.modules.users import repository as users_repository
from app.core import security


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


@router.websocket("/ws")
async def notifications_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    # Expect access token in query params: ?token=...
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = security.decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user = users_repository.get_by_id(db, user_id)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    last_seen = datetime.now(timezone.utc)
    try:
        while True:
            # poll for new notifications every 5 seconds
            new_items = service.list_since(db, user_id=user.id, since=last_seen, limit=50)
            if new_items:
                last_seen = max(n.created_at for n in new_items if n.created_at)
                await websocket.send_json(
                    [
                        {
                            "id": str(n.id),
                            "type": n.type,
                            "title": n.title,
                            "body": n.body,
                            "is_read": n.is_read,
                            "created_at": n.created_at.isoformat() if n.created_at else None,
                        }
                        for n in new_items
                    ]
                )
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
