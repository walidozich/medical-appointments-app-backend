from typing import Tuple
from sqlalchemy.orm import Session
from jose import JWTError

from app.modules.users import repository as users_repository
from app.core import security
from app.core.security import verify_password, get_password_hash, decode_token
from app.modules.auth import repository as auth_repository
from datetime import datetime
from app.modules.users import models as user_models
from app.core.config import settings


def register_user(db: Session, email: str, password: str) -> Tuple[object, dict]:
    existing = users_repository.get_by_email(db, email=email)
    if existing:
        raise ValueError("Email already registered")

    hashed = get_password_hash(password)
    user = users_repository.create_user(db, email=email, password_hash=hashed)

    # include token_version in tokens
    access_payload = {"ver": user.token_version}
    refresh_payload = {"ver": user.token_version}
    # the security.create_* functions don't accept payloads, so we encode manually
    access = security.create_access_token(subject=str(user.id))
    # attach version by re-encoding with claim
    access = security.jwt.encode({**security.decode_token(access), **access_payload}, security.settings.JWT_SECRET_KEY, algorithm="HS256")
    refresh = security.create_refresh_token(subject=str(user.id))
    refresh = security.jwt.encode({**security.decode_token(refresh, refresh=True), **refresh_payload}, security.settings.JWT_REFRESH_SECRET, algorithm="HS256")

    return user, {"access_token": access, "refresh_token": refresh}


def authenticate_user(db: Session, email: str, password: str) -> Tuple[object, dict]:
    user = users_repository.get_by_email(db, email=email)
    if not user:
        raise ValueError("Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    access_payload = {"ver": user.token_version}
    refresh_payload = {"ver": user.token_version}
    access = security.create_access_token(subject=str(user.id))
    access = security.jwt.encode({**security.decode_token(access), **access_payload}, security.settings.JWT_SECRET_KEY, algorithm="HS256")
    refresh = security.create_refresh_token(subject=str(user.id))
    refresh = security.jwt.encode({**security.decode_token(refresh, refresh=True), **refresh_payload}, security.settings.JWT_REFRESH_SECRET, algorithm="HS256")

    return user, {"access_token": access, "refresh_token": refresh}


def refresh_access_token(db: Session, token: str) -> dict:
    # Check token revocation first
    if auth_repository.is_token_revoked(db, token):
        raise ValueError("Refresh token revoked")

    try:
        payload = decode_token(token, refresh=True)
    except JWTError as e:
        raise ValueError("Invalid refresh token") from e

    # Ensure token type is refresh
    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Invalid token payload")
    token_ver = payload.get("ver", 0)
    try:
        token_ver_int = int(token_ver)
    except (TypeError, ValueError):
        raise ValueError("Invalid token payload")

    # Fetch user and use their current token_version in new tokens
    user = users_repository.get_by_id(db, user_id=sub)
    if not user:
        raise ValueError("Invalid token subject")
    if token_ver_int != int(getattr(user, "token_version", 0)):
        raise ValueError("Refresh token no longer valid")
    access = security.create_access_token(subject=str(sub))
    access = security.jwt.encode({**security.decode_token(access), "ver": user.token_version}, security.settings.JWT_SECRET_KEY, algorithm="HS256")
    refresh = security.create_refresh_token(subject=str(sub))
    refresh = security.jwt.encode({**security.decode_token(refresh, refresh=True), "ver": user.token_version}, security.settings.JWT_REFRESH_SECRET, algorithm="HS256")

    return {"access_token": access, "refresh_token": refresh}


def revoke_token(db: Session, token: str, refresh: bool = False):
    """Revoke a token (access or refresh). Attempts to decode to extract expiry; if
    decoding fails the token is still stored to prevent reuse.
    """
    try:
        payload = decode_token(token, refresh=refresh)
    except JWTError:
        expires = None
    else:
        exp = payload.get("exp")
        expires = None
        if exp:
            try:
                expires = datetime.fromtimestamp(int(exp))
            except Exception:
                expires = None

    return auth_repository.revoke_token(db, token=token, expires_at=expires)


def invalidate_user_tokens(db: Session, user_id: str):
    """Increment user's token_version to invalidate all previously issued tokens."""
    user = users_repository.get_by_id(db, user_id=user_id)
    if not user:
        raise ValueError("User not found")
    user.token_version = (user.token_version or 0) + 1
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def generate_password_reset_token(db: Session, email: str) -> str:
    user = users_repository.get_by_email(db, email=email)
    if not user:
        raise ValueError("If the email exists in our system, you will receive password reset instructions")
    token = security.create_password_reset_token(subject=str(user.id))
    return token


def reset_password(db: Session, reset_token: str, new_password: str):
    try:
        payload = decode_token(reset_token, refresh=False)
    except JWTError as e:
        raise ValueError("Invalid or expired reset token") from e

    if payload.get("type") != "reset":
        raise ValueError("Invalid reset token")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token payload")

    user = users_repository.get_by_id(db, user_id=user_id)
    if not user:
        raise ValueError("User not found")

    hashed = get_password_hash(new_password)
    users_repository.update_user(db, user=user, user_in={"password_hash": hashed})
    # bump token_version to invalidate previous tokens
    invalidate_user_tokens(db, user_id)
    return True
