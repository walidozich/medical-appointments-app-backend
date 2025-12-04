from sqlalchemy.orm import Session
from . import repository, models, schemas
from app.core.security import get_password_hash

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return repository.get_users(db=db, skip=skip, limit=limit)

def update_user(db: Session, user: models.User, user_in: schemas.UserUpdate):
    user_data = user_in.model_dump(exclude_unset=True)
    if "email" in user_data and user_data["email"] and user_data["email"] != user.email:
        existing = repository.get_by_email(db, email=user_data["email"])
        if existing and existing.id != user.id:
            raise ValueError("Email already in use")
    if "password" in user_data and user_data["password"]:
        user_data["password_hash"] = get_password_hash(user_data["password"])
        del user_data["password"]
    if "role" in user_data:
        if user_data["role"]:
            role_obj = repository.get_role_by_name(db, user_data["role"])
            if not role_obj:
                raise ValueError("Invalid role")
            user_data["role_id"] = role_obj.id
        del user_data["role"]
    
    return repository.update_user(db, user=user, user_in=user_data)
