from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.modules.users import models as user_models
from app.modules.patients import models as patient_models
from app.modules.doctors import models as doctor_models
from app.modules.appointments import models as appt_models
from app.modules.billing import models as billing_models


def summary(db: Session) -> dict:
    total_users = db.query(func.count(user_models.User.id)).scalar() or 0
    active_users = (
        db.query(func.count(user_models.User.id))
        .filter(user_models.User.is_active.is_(True))
        .scalar()
        or 0
    )
    roles_breakdown = dict(
        db.query(user_models.Role.name, func.count(user_models.User.id))
        .join(user_models.User)
        .group_by(user_models.Role.name)
        .all()
    )

    patients_count = db.query(func.count(patient_models.Patient.id)).scalar() or 0
    doctors_count = db.query(func.count(doctor_models.Doctor.id)).scalar() or 0

    appt_counts = dict(
        db.query(appt_models.Appointment.status, func.count(appt_models.Appointment.id))
        .group_by(appt_models.Appointment.status)
        .all()
    )
    total_appointments = sum(appt_counts.values()) if appt_counts else 0

    billing_paid = (
        db.query(func.coalesce(func.sum(billing_models.Billing.amount), 0))
        .filter(billing_models.Billing.status == "PAID")
        .scalar()
    )
    billing_pending = (
        db.query(func.coalesce(func.sum(billing_models.Billing.amount), 0))
        .filter(billing_models.Billing.status == "PENDING")
        .scalar()
    )

    return {
        "users": {
            "total": int(total_users),
            "active": int(active_users),
            "by_role": {k: int(v) for k, v in roles_breakdown.items()},
        },
        "profiles": {
            "patients": int(patients_count),
            "doctors": int(doctors_count),
        },
        "appointments": {
            "total": int(total_appointments),
            "by_status": {k: int(v) for k, v in appt_counts.items()},
        },
        "billing": {
            "paid_total": float(billing_paid or 0),
            "pending_total": float(billing_pending or 0),
        },
    }
