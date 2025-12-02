from sqlalchemy.orm import Session

from app.modules.users import models as user_models


def get_by_email(db: Session, email: str):
    return db.query(user_models.User).filter(user_models.User.email == email).first()


def get_by_id(db: Session, user_id):
    return db.query(user_models.User).filter(user_models.User.id == user_id).first()


def create_user(db: Session, *, email: str, password_hash: str):
    user = user_models.User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
