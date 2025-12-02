from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.modules.users.schemas import UserRead, UserUpdate
from app.modules.users.models import User
from . import service, repository

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user

@router.get("/", response_model=List[UserRead])
def read_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_active_user)):
    """
    Retrieve users.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    users = service.get_users(db, skip=skip, limit=limit)
    return users

@router.patch("/me", response_model=UserRead)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update own user.
    """
    user = service.update_user(db, user=current_user, user_in=user_in)
    return user

@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a user.
    """
    user = repository.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this username does not exist in the system",
        )
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    user = service.update_user(db, user=user, user_in=user_in)
    return user
