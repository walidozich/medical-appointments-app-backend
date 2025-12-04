from sqlalchemy.orm import Session

from app.modules.patients import models


def get_by_id(db: Session, patient_id):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()


def get_by_user_id(db: Session, user_id):
    return db.query(models.Patient).filter(models.Patient.user_id == user_id).first()


def list_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()


def create_patient(db: Session, patient_in: dict):
    patient = models.Patient(**patient_in)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient: models.Patient, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(patient, field, value)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient: models.Patient):
    db.delete(patient)
    db.commit()
