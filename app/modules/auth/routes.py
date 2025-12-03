from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.auth import schemas, service

router = APIRouter()


@router.post("/register", response_model=schemas.Token)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        user, tokens = service.register_user(db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return schemas.Token(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        user, tokens = service.authenticate_user(db, email=payload.email, password=payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return schemas.Token(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])

@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_refresh_token: Optional[str] = Header(None, alias="X-Refresh-Token"),
):
    """
    Logout endpoint that does not require a request body.

    Behavior:
    - If header `X-Refresh-Token` is provided, revoke that refresh token.
    - If an `Authorization: Bearer <access_token>` header is present, revoke the access token.
    - If neither is present, return success (idempotent logout for client-side state clearing).
    """
    # Revoke refresh token provided in custom header
    if x_refresh_token:
        try:
            # revoke the refresh token and rotate user's token_version to invalidate all tokens
            service.revoke_token(db, x_refresh_token, refresh=True)
            # attempt to decode to get subject and rotate token_version for that user
            try:
                from app.core import security as _sec
                payload = _sec.decode_token(x_refresh_token, refresh=True)
                sub = payload.get("sub")
                if sub:
                    service.invalidate_user_tokens(db, sub)
            except Exception:
                # If decoding fails, still proceed — we revoked the token string itself
                pass
        except ValueError:
            pass

    # Try to read Authorization header for access token (optional)
    access_header = authorization
    if access_header:
        parts = access_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            access_token = parts[1]
            try:
                service.revoke_token(db, access_token, refresh=False)
            except ValueError:
                pass

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=schemas.Token)
def refresh(payload: schemas.RefreshRequest, db: Session = Depends(get_db)):
    """Expects JSON payload: { \"refresh_token\": \"...\" }"""
    refresh_token = payload.refresh_token
    try:
        tokens = service.refresh_access_token(db, refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return schemas.Token(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"])


@router.post("/forgot")
def forgot_password(payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    """Generate a password reset token and (in DEBUG) return it. In production this should send an email."""
    try:
        token = service.generate_password_reset_token(db, payload.email)
    except ValueError:
        # don't reveal whether email exists
        return {"message": "If the email exists in our system, you will receive password reset instructions"}

    # In DEBUG, return the token so testing is easy. In production, send via email and don't return token.
    from app.core.config import settings
    if settings.DEBUG:
        return {"reset_token": token}
    # TODO: send email via configured mailer
    return {"message": "If the email exists in our system, you will receive password reset instructions"}


@router.post("/reset")
def reset_password(payload: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    try:
        service.reset_password(db, payload.reset_token, payload.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "Password reset successful"}
