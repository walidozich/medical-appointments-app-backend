from typing import List, Optional
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.modules.doctors import service, schemas
from app.modules.users.models import User

router = APIRouter()


@router.get("/", response_model=List[schemas.DoctorRead])
def list_doctors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    min_rating: Optional[float] = None,
):
    doctors = service.list_doctors(
        db,
        skip=skip,
        limit=limit,
        name=name,
        specialty=specialty,
        city=city,
        min_rating=min_rating,
    )
    return doctors


@router.get("/{doctor_id}", response_model=schemas.DoctorRead)
def get_doctor(doctor_id: UUID, db: Session = Depends(get_db)):
    try:
        doctor = service.get_doctor(db, doctor_id=doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return doctor


@router.post("/", response_model=schemas.DoctorRead, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: schemas.DoctorCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    try:
        doctor = service.create_doctor(db, user_id=payload.user_id, doctor_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return doctor


@router.get("/me/profile", response_model=schemas.DoctorRead)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    try:
        doctor = service.get_doctor_by_user(db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return doctor


@router.post("/me/profile", response_model=schemas.DoctorRead, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    payload: schemas.DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    try:
        doctor = service.create_doctor(db, user_id=current_user.id, doctor_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return doctor


@router.patch("/me/profile", response_model=schemas.DoctorRead)
def update_my_profile(
    payload: schemas.DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("DOCTOR", "ADMIN")),
):
    try:
        doctor = service.update_doctor_for_user(db, user_id=current_user.id, doctor_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return doctor


@router.patch("/{doctor_id}", response_model=schemas.DoctorRead)
def update_doctor(
    doctor_id: UUID,
    payload: schemas.DoctorUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        doctor = service.update_doctor(db, doctor_id=doctor_id, doctor_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        service.delete_doctor(db, doctor_id=doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None


@router.get("/{doctor_id}/availability", response_model=List[schemas.DoctorAvailabilityRead])
def list_availability(doctor_id: UUID, db: Session = Depends(get_db)):
    return service.list_availability(db, doctor_id=doctor_id)


@router.post("/{doctor_id}/availability", response_model=schemas.DoctorAvailabilityRead, status_code=status.HTTP_201_CREATED)
def create_availability(
    doctor_id: UUID,
    payload: schemas.DoctorAvailabilityCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.create_availability(db, doctor_id=doctor_id, availability_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/availability/{availability_id}", response_model=schemas.DoctorAvailabilityRead)
def update_availability(
    availability_id: UUID,
    payload: schemas.DoctorAvailabilityUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.update_availability(db, availability_id=availability_id, availability_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/availability/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(
    availability_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        service.delete_availability(db, availability_id=availability_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None


@router.get("/{doctor_id}/availability/slots", response_model=List[schemas.AvailabilitySlotRead])
def list_available_slots(
    doctor_id: UUID,
    start_date: Optional[str] = None,
    days: int = 7,
    slot_minutes: int = 30,
    db: Session = Depends(get_db),
):
    try:
        if start_date:
            parsed_start = date.fromisoformat(start_date)
        else:
            parsed_start = date.today()
        if days < 1:
            raise ValueError("days must be >= 1")
        if slot_minutes < 5:
            raise ValueError("slot_minutes must be >= 5")
        slots = service.list_available_slots(
            db,
            doctor_id=doctor_id,
            start_date=parsed_start,
            days=days,
            slot_minutes=slot_minutes,
        )
        return slots
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{doctor_id}/favorite", response_model=schemas.FavoriteRead, status_code=status.HTTP_201_CREATED)
def add_favorite(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT")),
):
    try:
        return service.add_favorite(db, doctor_id=doctor_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{doctor_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT")),
):
    try:
        service.remove_favorite(db, doctor_id=doctor_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None


@router.get("/me/favorites", response_model=List[schemas.DoctorRead])
def list_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT")),
):
    try:
        return service.list_favorites(db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{doctor_id}/reviews", response_model=List[schemas.ReviewRead])
def list_reviews(doctor_id: UUID, db: Session = Depends(get_db)):
    try:
        return service.list_reviews(db, doctor_id=doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{doctor_id}/reviews", response_model=schemas.ReviewRead, status_code=status.HTTP_201_CREATED)
def add_review(
    doctor_id: UUID,
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT")),
):
    try:
        return service.add_review(db, doctor_id=doctor_id, user_id=current_user.id, review_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
