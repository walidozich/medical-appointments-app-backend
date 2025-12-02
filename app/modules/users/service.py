from sqlalchemy.orm import Session
from . import repository, models, schemas
from app.core.security import get_password_hash

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return repository.get_users(db=db, skip=skip, limit=limit)

def update_user(db: Session, user: models.User, user_in: schemas.UserUpdate):
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data and user_data["password"]:
        user_data["password_hash"] = get_password_hash(user_data["password"])
        del user_data["password"]
    
    return repository.update_user(db, user=user, user_in=user_data)
