from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.modules.users.models import User
from app.core import security
from app.modules.users import repository as users_repository
from app.modules.auth import repository as auth_repository

reusable_oauth2 = HTTPBearer(
    scheme_name="Bearer"
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token.credentials)
        user_id: str = payload.get("sub")
        token_ver = payload.get("ver")
        if user_id is None:
            raise credentials_exception
        # Check if access token was revoked
        if auth_repository.is_token_revoked(db, token.credentials):
            raise credentials_exception
        # Check token version matches user's current token_version
        user = users_repository.get_by_id(db, user_id=user_id)
        if user is None:
            raise credentials_exception
        if token_ver is not None and getattr(user, "token_version", 0) != int(token_ver):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # user was already loaded above if needed
    # Ensure user is loaded when token didn't contain ver
    if 'user' not in locals():
        user = users_repository.get_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user