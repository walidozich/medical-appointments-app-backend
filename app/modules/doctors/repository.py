from typing import List, Sequence
from sqlalchemy.orm import Session

from app.modules.doctors import models


def get_doctor(db: Session, doctor_id):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()


def get_doctor_by_user(db: Session, user_id):
    return db.query(models.Doctor).filter(models.Doctor.user_id == user_id).first()


def list_doctors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Doctor).offset(skip).limit(limit).all()


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
