from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.modules.chat import service, schemas
from app.modules.users.models import User
from app.modules.users import repository as users_repository
from app.core import security
from app.modules.chat.repository import get_thread
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository


router = APIRouter()


@router.get("/threads", response_model=List[schemas.ChatThreadRead])
def list_threads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return service.list_threads(db, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/threads", response_model=schemas.ChatThreadRead, status_code=status.HTTP_201_CREATED)
def create_thread(
    payload: schemas.ChatThreadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return service.get_or_create_thread(db, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/threads/{thread_id}/messages", response_model=List[schemas.ChatMessageRead])
def list_messages(
    thread_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return service.list_messages(db, current_user, thread_id=thread_id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/threads/{thread_id}/messages", response_model=schemas.ChatMessageRead, status_code=status.HTTP_201_CREATED)
def post_message(
    thread_id: UUID,
    payload: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return service.post_message(db, current_user, thread_id=thread_id, msg_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Simple in-memory connection manager (per-process)
class ConnectionManager:
    def __init__(self):
        self.active: dict[UUID, list[WebSocket]] = {}

    async def connect(self, thread_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(thread_id, []).append(websocket)

    def disconnect(self, thread_id: UUID, websocket: WebSocket):
        if thread_id in self.active:
            self.active[thread_id] = [ws for ws in self.active[thread_id] if ws is not websocket]
            if not self.active[thread_id]:
                self.active.pop(thread_id, None)

    async def broadcast(self, thread_id: UUID, message: dict):
        for ws in self.active.get(thread_id, []):
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: UUID, db: Session = Depends(get_db)):
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

    thread = get_thread(db, thread_id)
    if not thread:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    role = getattr(user, "role_name", "").upper()
    if role == "PATIENT":
        patient = patients_repository.get_by_user_id(db, user.id)
        if not patient or patient.id != thread.patient_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    elif role == "DOCTOR":
        doctor = doctors_repository.get_doctor_by_user(db, user_id=user.id)
        if not doctor or doctor.id != thread.doctor_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    else:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(thread_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                continue
            try:
                msg = service.post_message(db, user, thread_id=thread_id, msg_in=schemas.ChatMessageCreate(content=content))
            except ValueError:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            await manager.broadcast(
                thread_id,
                {
                    "id": str(msg.id),
                    "thread_id": str(msg.thread_id),
                    "sender_id": str(msg.sender_id),
                    "sender_role": msg.sender_role,
                    "content": msg.content,
                    "sent_at": msg.sent_at.isoformat(),
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(thread_id, websocket)
