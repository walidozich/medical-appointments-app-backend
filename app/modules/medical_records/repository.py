from sqlalchemy.orm import Session
from app.modules.medical_records import models


def get_by_id(db: Session, record_id):
    return db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()


def list_by_patient(db: Session, patient_id, skip: int = 0, limit: int = 100):
    return (
        db.query(models.MedicalRecord)
        .filter(models.MedicalRecord.patient_id == patient_id)
        .order_by(models.MedicalRecord.recorded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_by_doctor(db: Session, doctor_id, skip: int = 0, limit: int = 100):
    return (
        db.query(models.MedicalRecord)
        .filter(models.MedicalRecord.doctor_id == doctor_id)
        .order_by(models.MedicalRecord.recorded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_record(db: Session, payload: dict):
    rec = models.MedicalRecord(**payload)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def update_record(db: Session, record: models.MedicalRecord, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(record, field, value)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record: models.MedicalRecord):
    db.delete(record)
    db.commit()
