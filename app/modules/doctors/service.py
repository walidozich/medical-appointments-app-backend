from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.modules.doctors import repository, schemas
from app.modules.users import repository as users_repository
from app.modules.patients import repository as patients_repository


def _ensure_user_is_doctor(db: Session, user_id: UUID):
    user = users_repository.get_by_id(db, user_id=user_id)
    if not user:
        raise ValueError("User not found")
    role_name = getattr(user, "role_name", None)
    if not role_name or role_name.upper() != "DOCTOR":
        raise ValueError("User is not a doctor")
    return user


def list_doctors(
    db: Session,
    *,
    name: str | None = None,
    specialty: str | None = None,
    city: str | None = None,
    min_rating: float | None = None,
    skip: int = 0,
    limit: int = 100,
):
    if any([name, specialty, city, min_rating is not None]):
        return repository.search_doctors(
            db,
            name=name,
            specialty=specialty,
            city=city,
            min_rating=min_rating,
            skip=skip,
            limit=limit,
        )
    return repository.list_doctors(db, skip=skip, limit=limit)


def get_doctor(db: Session, doctor_id: UUID):
    doctor = repository.get_doctor(db, doctor_id=doctor_id)
    if not doctor:
        raise ValueError("Doctor not found")
    return doctor


def get_doctor_by_user(db: Session, user_id: UUID):
    doctor = repository.get_doctor_by_user(db, user_id=user_id)
    if not doctor:
        raise ValueError("Doctor not found")
    return doctor


def create_doctor(db: Session, user_id: UUID, doctor_in: schemas.DoctorCreate):
    _ensure_user_is_doctor(db, user_id)
    existing = repository.get_doctor_by_user(db, user_id=user_id)
    if existing:
        raise ValueError("Doctor profile already exists")
    payload = doctor_in.model_dump(exclude_unset=True)
    payload["user_id"] = user_id
    specialty_names = payload.pop("specialties", None)
    return repository.create_doctor(db, doctor_in=payload, specialty_names=specialty_names)


def update_doctor(db: Session, doctor_id: UUID, doctor_in: schemas.DoctorUpdate):
    doctor = get_doctor(db, doctor_id)
    updates = doctor_in.model_dump(exclude_unset=True)
    specialty_names = updates.pop("specialties", None) if "specialties" in updates else None
    return repository.update_doctor(db, doctor=doctor, updates=updates, specialty_names=specialty_names)


def update_doctor_for_user(db: Session, user_id: UUID, doctor_in: schemas.DoctorUpdate):
    doctor = repository.get_doctor_by_user(db, user_id=user_id)
    if not doctor:
        raise ValueError("Doctor not found")
    updates = doctor_in.model_dump(exclude_unset=True)
    specialty_names = updates.pop("specialties", None) if "specialties" in updates else None
    return repository.update_doctor(db, doctor=doctor, updates=updates, specialty_names=specialty_names)


def delete_doctor(db: Session, doctor_id: UUID):
    doctor = get_doctor(db, doctor_id)
    repository.delete_doctor(db, doctor=doctor)
    return True


def list_availability(db: Session, doctor_id: UUID):
    return repository.list_availability(db, doctor_id=doctor_id)


def create_availability(db: Session, doctor_id: UUID, availability_in: schemas.DoctorAvailabilityCreate):
    doctor = get_doctor(db, doctor_id)
    payload = availability_in.model_dump(exclude_unset=True)
    payload["doctor_id"] = doctor.id
    return repository.create_availability(db, payload)


def update_availability(db: Session, availability_id: UUID, availability_in: schemas.DoctorAvailabilityUpdate, doctor_id: UUID | None = None):
    availability = repository.get_availability(db, availability_id)
    if not availability:
        raise ValueError("Availability not found")
    if doctor_id and availability.doctor_id != doctor_id:
        raise ValueError("Cannot modify another doctor's availability")
    updates = availability_in.model_dump(exclude_unset=True)
    return repository.update_availability(db, availability=availability, updates=updates)


def delete_availability(db: Session, availability_id: UUID, doctor_id: UUID | None = None):
    availability = repository.get_availability(db, availability_id)
    if not availability:
        raise ValueError("Availability not found")
    if doctor_id and availability.doctor_id != doctor_id:
        raise ValueError("Cannot delete another doctor's availability")
    repository.delete_availability(db, availability=availability)
    return True


def _get_patient_for_user(db: Session, user_id: UUID):
    patient = patients_repository.get_by_user_id(db, user_id=user_id)
    if not patient:
        raise ValueError("Patient profile not found")
    return patient


def add_favorite(db: Session, doctor_id: UUID, user_id: UUID):
    doctor = get_doctor(db, doctor_id)
    patient = _get_patient_for_user(db, user_id)
    return repository.toggle_favorite(db, patient_id=patient.id, doctor_id=doctor.id, add=True)


def remove_favorite(db: Session, doctor_id: UUID, user_id: UUID):
    doctor = get_doctor(db, doctor_id)
    patient = _get_patient_for_user(db, user_id)
    repository.toggle_favorite(db, patient_id=patient.id, doctor_id=doctor.id, add=False)
    return True


def list_favorites(db: Session, user_id: UUID):
    patient = _get_patient_for_user(db, user_id)
    return repository.list_favorites(db, patient_id=patient.id)


def add_review(db: Session, doctor_id: UUID, user_id: UUID, review_in: schemas.ReviewCreate):
    doctor = get_doctor(db, doctor_id)
    patient = _get_patient_for_user(db, user_id)
    data = review_in.model_dump()
    return repository.create_review(db, patient_id=patient.id, doctor_id=doctor.id, rating=data["rating"], comment=data.get("comment"))


def list_reviews(db: Session, doctor_id: UUID):
    doctor = get_doctor(db, doctor_id)
    return repository.list_reviews(db, doctor.id)
