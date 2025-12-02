from typing import Tuple
from sqlalchemy.orm import Session
from jose import JWTError

from app.modules.users import repository as users_repository
from app.core import security
from app.core.security import verify_password, get_password_hash, decode_token


def register_user(db: Session, email: str, password: str) -> Tuple[object, dict]:
    existing = users_repository.get_by_email(db, email=email)
    if existing:
        raise ValueError("Email already registered")

    hashed = get_password_hash(password)
    user = users_repository.create_user(db, email=email, password_hash=hashed)

    access = security.create_access_token(subject=str(user.id))
    refresh = security.create_refresh_token(subject=str(user.id))

    return user, {"access_token": access, "refresh_token": refresh}


def authenticate_user(db: Session, email: str, password: str) -> Tuple[object, dict]:
    user = users_repository.get_by_email(db, email=email)
    if not user:
        raise ValueError("Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    access = security.create_access_token(subject=str(user.id))
    refresh = security.create_refresh_token(subject=str(user.id))

    return user, {"access_token": access, "refresh_token": refresh}


def refresh_access_token(token: str) -> dict:
    try:
        payload = decode_token(token, refresh=True)
    except JWTError as e:
        raise ValueError("Invalid refresh token") from e

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Invalid token payload")

    access = security.create_access_token(subject=str(sub))
    refresh = security.create_refresh_token(subject=str(sub))

    return {"access_token": access, "refresh_token": refresh}
