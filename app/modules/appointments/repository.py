from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.modules.appointments import models


def list_appointments_for_patient(db: Session, patient_id, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.patient_id == patient_id)
        .order_by(models.Appointment.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_appointments_for_doctor(db: Session, doctor_id, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Appointment)
        .filter(models.Appointment.doctor_id == doctor_id)
        .order_by(models.Appointment.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_id(db: Session, appointment_id):
    return db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()


def has_conflict(db: Session, doctor_id, start_time: datetime, end_time: datetime) -> bool:
    conflict = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == "SCHEDULED",
            or_(
                and_(models.Appointment.start_time <= start_time, models.Appointment.end_time > start_time),
                and_(models.Appointment.start_time < end_time, models.Appointment.end_time >= end_time),
                and_(models.Appointment.start_time >= start_time, models.Appointment.end_time <= end_time),
            ),
        )
        .first()
    )
    return conflict is not None


def list_scheduled_for_doctor_between(db: Session, doctor_id, start_time: datetime, end_time: datetime):
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == "SCHEDULED",
            models.Appointment.start_time < end_time,
            models.Appointment.end_time > start_time,
        )
        .all()
    )


def create_appointment(db: Session, payload: dict):
    appt = models.Appointment(**payload)
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def update_appointment(db: Session, appointment: models.Appointment, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(appointment, field, value)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
