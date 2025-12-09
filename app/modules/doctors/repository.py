from typing import List, Sequence
from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.doctors import models


def get_doctor(db: Session, doctor_id):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()


def get_doctor_by_user(db: Session, user_id):
    return db.query(models.Doctor).filter(models.Doctor.user_id == user_id).first()


def list_doctors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Doctor).offset(skip).limit(limit).all()


def search_doctors(
    db: Session,
    *,
    name: str | None = None,
    specialty: str | None = None,
    city: str | None = None,
    min_rating: float | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(models.Doctor)

    if specialty:
        query = query.join(models.Doctor.specialties).filter(func.lower(models.Specialty.name) == specialty.lower())
    if city:
        query = query.filter(func.lower(models.Doctor.city) == city.lower())
    if name:
        lowered = f"%{name.lower()}%"
        query = query.filter(
            func.lower(models.Doctor.first_name).like(lowered) | func.lower(models.Doctor.last_name).like(lowered)
        )
    if min_rating is not None:
        query = query.filter(models.Doctor.avg_rating >= min_rating)

    return query.distinct().offset(skip).limit(limit).all()


def upsert_specialties(db: Session, names: Sequence[str]):
    existing = db.query(models.Specialty).filter(models.Specialty.name.in_([n.upper() for n in names])).all()
    existing_map = {s.name.upper(): s for s in existing}
    specialties: List[models.Specialty] = []
    for name in names:
        key = name.upper()
        if key in existing_map:
            specialties.append(existing_map[key])
        else:
            spec = models.Specialty(name=key.title() if name.isupper() else name, description=None)
            db.add(spec)
            db.flush()
            specialties.append(spec)
    db.commit()
    return specialties


def create_doctor(db: Session, doctor_in: dict, specialty_names=None):
    doctor = models.Doctor(**doctor_in)
    db.add(doctor)
    db.flush()
    if specialty_names:
        doctor.specialties = upsert_specialties(db, specialty_names)
    db.commit()
    db.refresh(doctor)
    return doctor


def update_doctor(db: Session, doctor: models.Doctor, updates: dict, specialty_names=None):
    for field, value in updates.items():
        if value is not None:
            setattr(doctor, field, value)
    if specialty_names is not None:
        doctor.specialties = upsert_specialties(db, specialty_names) if specialty_names else []
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def delete_doctor(db: Session, doctor: models.Doctor):
    db.delete(doctor)
    db.commit()


def list_availability(db: Session, doctor_id):
    return db.query(models.DoctorAvailability).filter(models.DoctorAvailability.doctor_id == doctor_id).all()


def get_availability(db: Session, availability_id):
    return db.query(models.DoctorAvailability).filter(models.DoctorAvailability.id == availability_id).first()


def create_availability(db: Session, availability_in: dict):
    avail = models.DoctorAvailability(**availability_in)
    db.add(avail)
    db.commit()
    db.refresh(avail)
    return avail


def update_availability(db: Session, availability: models.DoctorAvailability, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(availability, field, value)
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


def delete_availability(db: Session, availability: models.DoctorAvailability):
    db.delete(availability)
    db.commit()


def toggle_favorite(db: Session, *, patient_id: UUID, doctor_id: UUID, add: bool = True) -> models.FavoriteDoctor | None:
    existing = (
        db.query(models.FavoriteDoctor)
        .filter(models.FavoriteDoctor.patient_id == patient_id, models.FavoriteDoctor.doctor_id == doctor_id)
        .first()
    )
    if add:
        if existing:
            return existing
        fav = models.FavoriteDoctor(patient_id=patient_id, doctor_id=doctor_id)
        db.add(fav)
        db.commit()
        db.refresh(fav)
        return fav
    if existing:
        db.delete(existing)
        db.commit()
    return None


def list_favorites(db: Session, *, patient_id: UUID):
    return (
        db.query(models.Doctor)
        .join(models.FavoriteDoctor, models.FavoriteDoctor.doctor_id == models.Doctor.id)
        .filter(models.FavoriteDoctor.patient_id == patient_id)
        .all()
    )


def create_review(db: Session, *, patient_id: UUID, doctor_id: UUID, rating: int, comment: str | None):
    review = models.Review(patient_id=patient_id, doctor_id=doctor_id, rating=rating, comment=comment)
    db.add(review)
    db.flush()
    # update aggregates
    stats = (
        db.query(func.count(models.Review.id), func.avg(models.Review.rating))
        .filter(models.Review.doctor_id == doctor_id)
        .one()
    )
    doc = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doc:
        doc.rating_count = int(stats[0] or 0)
        doc.avg_rating = float(stats[1] or 0)
        db.add(doc)
    db.commit()
    db.refresh(review)
    return review


def list_reviews(db: Session, doctor_id: UUID):
    return db.query(models.Review).filter(models.Review.doctor_id == doctor_id).order_by(models.Review.created_at.desc()).all()


def get_review(db: Session, review_id: UUID):
    return db.query(models.Review).filter(models.Review.id == review_id).first()


# Specialty admin helpers
def list_specialties(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Specialty).order_by(models.Specialty.name.asc()).offset(skip).limit(limit).all()


def get_specialty(db: Session, specialty_id: int):
    return db.query(models.Specialty).filter(models.Specialty.id == specialty_id).first()


def create_specialty(db: Session, data: dict):
    spec = models.Specialty(**data)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def update_specialty(db: Session, specialty: models.Specialty, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(specialty, field, value)
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    return specialty


def delete_specialty(db: Session, specialty: models.Specialty):
    db.delete(specialty)
    db.commit()


def list_all_reviews(
    db: Session,
    *,
    doctor_id: UUID | None = None,
    patient_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(models.Review)
    if doctor_id:
        query = query.filter(models.Review.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(models.Review.patient_id == patient_id)
    return query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()


def delete_review(db: Session, review: models.Review):
    db.delete(review)
    db.commit()
