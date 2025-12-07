from typing import List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi import UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.core import security
from app.modules.chat import service, schemas, models as chat_models
from app.modules.chat.repository import get_thread, add_message
from app.modules.users.models import User
from app.modules.users import repository as users_repository
from app.modules.patients import repository as patients_repository
from app.modules.doctors import repository as doctors_repository
from app.modules.chat import repository as chat_repository


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
    """Tracks active websocket connections per thread."""

    def __init__(self):
        self.active: Dict[UUID, List[WebSocket]] = {}

    async def connect(self, thread_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(thread_id, []).append(websocket)

    def disconnect(self, thread_id: UUID, websocket: WebSocket):
        conns = self.active.get(thread_id)
        if not conns:
            return
        self.active[thread_id] = [ws for ws in conns if ws is not websocket]
        if not self.active[thread_id]:
            self.active.pop(thread_id, None)

    async def broadcast(self, thread_id: UUID, message: dict):
        for ws in self.active.get(thread_id, []):
            await ws.send_json(message)


manager = ConnectionManager()


def _serialize_message(msg: chat_models.ChatMessage) -> dict:
    return {
        "id": str(msg.id),
        "thread_id": str(msg.thread_id),
        "sender_id": str(msg.sender_id),
        "sender_role": msg.sender_role,
        "content": msg.content,
        "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
        "read_at": msg.read_at.isoformat() if msg.read_at else None,
        "is_system_message": msg.is_system_message,
    }


def _extract_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return websocket.query_params.get("token")


def _ensure_participant(db: Session, user_id: UUID, thread: chat_models.ChatThread) -> str:
    user = users_repository.get_by_id(db, user_id=user_id)
    if not user:
        raise PermissionError("User not found")
    role = (user.role_name or "").upper()
    if role == "PATIENT":
        patient = patients_repository.get_by_user_id(db, user_id=user_id)
        if not patient or patient.id != thread.patient_id:
            raise PermissionError("Not a participant")
        return "PATIENT"
    if role == "DOCTOR":
        doctor = doctors_repository.get_doctor_by_user(db, user_id=user_id)
        if not doctor or doctor.id != thread.doctor_id:
            raise PermissionError("Not a participant")
        return "DOCTOR"
    raise PermissionError("Not allowed")


@router.websocket("/ws/chat/{thread_id}")
async def websocket_chat(websocket: WebSocket, thread_id: UUID, db: Session = Depends(get_db)):
    token = _extract_token(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        payload = security.decode_token(token)
        user_id = UUID(str(payload.get("sub")))
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    thread = get_thread(db, thread_id)
    if not thread or thread.status.lower() == "closed":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        sender_role = _ensure_participant(db, user_id, thread)
    except PermissionError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(thread_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                continue
            # re-check status
            thread = get_thread(db, thread_id)
            if not thread or thread.status.lower() == "closed":
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            msg = add_message(
                db,
                thread_id=thread.id,
                sender_id=user_id,
                sender_role=sender_role,
                content=content,
            )
            await manager.broadcast(thread_id, _serialize_message(msg))
    except WebSocketDisconnect:
        manager.disconnect(thread_id, websocket)


@router.patch("/messages/{message_id}/read", response_model=schemas.ChatMessageRead)
def mark_message_read(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        msg = service.mark_message_read(
            db,
            current_user,
            message_id=message_id,
            on_broadcast=lambda m: manager.broadcast(m.thread_id, _serialize_message(m)),
        )
        return msg
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/threads/{thread_id}/attachments", response_model=schemas.ChatMessageRead, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    thread_id: UUID,
    file: UploadFile = File(...),
    caption: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        msg = service.upload_attachment(db, current_user, thread_id=thread_id, file=file, caption=caption)
        return msg
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/threads/{thread_id}/status", response_model=schemas.ChatThreadRead)
def update_thread_status(
    thread_id: UUID,
    payload: schemas.ChatThreadStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return service.update_thread_status(db, current_user, thread_id=thread_id, status=payload.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
