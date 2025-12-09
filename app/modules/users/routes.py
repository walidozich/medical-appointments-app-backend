from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.modules.users.schemas import UserRead, UserUpdate, UserCreateAdmin
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
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_roles("ADMIN")),
):
    """
    Retrieve users.
    """
    users = service.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateAdmin,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    """
    Admin create user with role.
    """
    try:
        return service.create_user_admin(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    user = repository.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

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
    if user_in.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your role",
        )
    try:
        user = service.update_user(db, user=current_user, user_in=user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user

@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: UserUpdate,
    admin_user: User = Depends(require_roles("ADMIN")),
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
    try:
        user = service.update_user(db, user=user, user_in=user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user
