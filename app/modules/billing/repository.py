from sqlalchemy.orm import Session

from app.modules.billing import models


# Billing
def get_billing(db: Session, billing_id):
    return db.query(models.Billing).filter(models.Billing.id == billing_id).first()


def list_billing_for_patient(db: Session, patient_id, skip=0, limit=100):
    return (
        db.query(models.Billing)
        .filter(models.Billing.patient_id == patient_id)
        .order_by(models.Billing.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_billing(db: Session, payload: dict):
    bill = models.Billing(**payload)
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def update_billing(db: Session, billing: models.Billing, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(billing, field, value)
    db.add(billing)
    db.commit()
    db.refresh(billing)
    return billing


# Insurance policies
def get_policy(db: Session, policy_id):
    return db.query(models.InsurancePolicy).filter(models.InsurancePolicy.id == policy_id).first()


def list_policies_for_patient(db: Session, patient_id, skip=0, limit=100):
    return (
        db.query(models.InsurancePolicy)
        .filter(models.InsurancePolicy.patient_id == patient_id)
        .order_by(models.InsurancePolicy.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_policy(db: Session, payload: dict):
    policy = models.InsurancePolicy(**payload)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def update_policy(db: Session, policy: models.InsurancePolicy, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(policy, field, value)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def delete_policy(db: Session, policy: models.InsurancePolicy):
    db.delete(policy)
    db.commit()


# Insurance claims
def get_claim(db: Session, claim_id):
    return db.query(models.InsuranceClaim).filter(models.InsuranceClaim.id == claim_id).first()


def list_claims_for_policy(db: Session, policy_id, skip=0, limit=100):
    return (
        db.query(models.InsuranceClaim)
        .filter(models.InsuranceClaim.policy_id == policy_id)
        .order_by(models.InsuranceClaim.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_claim(db: Session, payload: dict):
    claim = models.InsuranceClaim(**payload)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def update_claim(db: Session, claim: models.InsuranceClaim, updates: dict):
    for field, value in updates.items():
        if value is not None:
            setattr(claim, field, value)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim
