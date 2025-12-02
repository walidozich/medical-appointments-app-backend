from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.auth import schemas, service
from app.modules.users.schemas import UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        user, tokens = service.register_user(db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        user, tokens = service.authenticate_user(db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return schemas.Token(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])

@router.post("/logout")
def logout():
    """
    Logout user.
    """
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=schemas.Token)
def refresh(token: dict, db: Session = Depends(get_db)):
    """Expects JSON payload: { "refresh_token": "..." }"""
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token required")
    try:
        tokens = service.refresh_access_token(refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return schemas.Token(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])