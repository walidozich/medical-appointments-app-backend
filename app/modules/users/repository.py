from sqlalchemy.orm import Session

from app.modules.users import models as user_models


def get_role_by_name(db: Session, name: str):
    if not name:
        return None
    return db.query(user_models.Role).filter(user_models.Role.name == name.upper()).first()


def get_default_role(db: Session) -> user_models.Role:
    role = get_role_by_name(db, "PATIENT")
    if not role:
        role = user_models.Role(name="PATIENT")
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def get_by_email(db: Session, email: str):
    return db.query(user_models.User).filter(user_models.User.email == email).first()


def get_by_id(db: Session, user_id):
    return db.query(user_models.User).filter(user_models.User.id == user_id).first()


def create_user(
    db: Session,
    *,
    email: str,
    password_hash: str,
    role_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
):
    role_obj = get_role_by_name(db, role_name) if role_name else None
    if not role_obj:
        role_obj = get_default_role(db)
    user = user_models.User(
        email=email,
        password_hash=password_hash,
        role_id=role_obj.id,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(user_models.User).offset(skip).limit(limit).all()

def update_user(db: Session, user: user_models.User, user_in: dict):
    for field, value in user_in.items():
        if value is not None:
            setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
