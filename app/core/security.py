from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_minutes: Optional[int] = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        # 'ver' will be filled by caller when available (token_version)
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def create_refresh_token(subject: str | Any, expires_days: Optional[int] = None) -> str:
    if expires_days is None:
        expires_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=expires_days)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        # 'ver' will be filled by caller when available (token_version)
    }
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm="HS256")


def create_password_reset_token(subject: str | Any, expires_minutes: Optional[int] = None) -> str:
    if expires_minutes is None:
        expires_minutes = 15

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "reset",
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token: str, refresh: bool = False) -> dict:
    secret = settings.JWT_REFRESH_SECRET if refresh else settings.JWT_SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except JWTError as e:
        # In the auth module, we will convert this to HTTPException(401)
        raise e