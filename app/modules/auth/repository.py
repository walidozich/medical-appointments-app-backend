from sqlalchemy.orm import Session

from app.modules.users import models as user_models
from app.modules.auth import models as auth_models
from datetime import datetime



def get_by_email(db: Session, email: str):
    return db.query(user_models.User).filter(user_models.User.email == email).first()


def get_by_id(db: Session, user_id):
    return db.query(user_models.User).filter(user_models.User.id == user_id).first()


def create_user(db: Session, *, email: str, password_hash: str):
    # Default to patient role if available
    from app.modules.users.repository import get_default_role
    default_role = get_default_role(db)
    user = user_models.User(email=email, password_hash=password_hash, role_id=default_role.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def revoke_token(db: Session, token: str, expires_at: datetime | None = None):
    revoked = auth_models.RevokedToken(token=token, expires_at=expires_at)
    db.add(revoked)
    db.commit()
    return revoked


def is_token_revoked(db: Session, token: str) -> bool:
    exists = db.query(auth_models.RevokedToken).filter(auth_models.RevokedToken.token == token).first()
    return exists is not None
