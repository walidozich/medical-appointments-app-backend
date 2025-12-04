from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.modules.patients import service, schemas
from app.modules.users.models import User

router = APIRouter()


@router.get("/", response_model=List[schemas.PatientRead])
def list_patients(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_roles("ADMIN")),
):
    patients = service.list_patients(db, skip=skip, limit=limit)
    return patients


@router.post("/", response_model=schemas.PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: schemas.PatientCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    try:
        patient = service.create_patient(db, user_id=payload.user_id, patient_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return patient


@router.get("/me", response_model=schemas.PatientRead)
def get_my_patient(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
):
    try:
        patient = service.get_patient_by_user(db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return patient


@router.post("/me", response_model=schemas.PatientRead, status_code=status.HTTP_201_CREATED)
def create_my_patient(
    payload: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
):
    try:
        patient = service.create_patient(db, user_id=current_user.id, patient_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return patient


@router.patch("/me", response_model=schemas.PatientRead)
def update_my_patient(
    payload: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
):
    try:
        patient = service.update_patient_for_user(db, user_id=current_user.id, patient_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return patient


@router.get("/{patient_id}", response_model=schemas.PatientRead)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        patient = service.get_patient(db, patient_id=patient_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return patient


@router.patch("/{patient_id}", response_model=schemas.PatientRead)
def update_patient(
    patient_id: UUID,
    payload: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        patient = service.update_patient(db, patient_id=patient_id, patient_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        service.delete_patient(db, patient_id=patient_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
