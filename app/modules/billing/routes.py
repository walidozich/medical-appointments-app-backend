from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.modules.billing import service, schemas
from app.modules.users.models import User
from app.modules.patients import repository as patients_repository

router = APIRouter()


# Billing
@router.post("/", response_model=schemas.BillingRead, status_code=status.HTTP_201_CREATED)
def create_billing(
    payload: schemas.BillingCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.create_billing(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{billing_id}", response_model=schemas.BillingRead)
def get_billing(
    billing_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.get_billing(db, billing_id=billing_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{billing_id}", response_model=schemas.BillingRead)
def update_billing(
    billing_id: UUID,
    payload: schemas.BillingUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.update_billing(db, billing_id=billing_id, payload=payload)
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/patient/{patient_id}", response_model=List[schemas.BillingRead])
def list_patient_billing(
    patient_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    try:
        return service.list_billing_for_patient(db, patient_id=patient_id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/me", response_model=List[schemas.BillingRead])
def list_my_billing(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return service.list_billing_for_patient(db, patient_id=patient.id, skip=skip, limit=limit)


# Insurance Policies
@router.post("/policies", response_model=schemas.InsurancePolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: schemas.InsurancePolicyCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.create_policy(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/policies/patient/{patient_id}", response_model=List[schemas.InsurancePolicyRead])
def list_patient_policies(
    patient_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    try:
        return service.list_policies_for_patient(db, patient_id=patient_id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/policies/me", response_model=List[schemas.InsurancePolicyRead])
def list_my_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("PATIENT", "ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    patient = patients_repository.get_by_user_id(db, user_id=current_user.id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return service.list_policies_for_patient(db, patient_id=patient.id, skip=skip, limit=limit)


@router.patch("/policies/{policy_id}", response_model=schemas.InsurancePolicyRead)
def update_policy(
    policy_id: UUID,
    payload: schemas.InsurancePolicyUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.update_policy(db, policy_id=policy_id, payload=payload)
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        service.delete_policy(db, policy_id=policy_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None


# Insurance Claims
@router.post("/claims", response_model=schemas.InsuranceClaimRead, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: schemas.InsuranceClaimCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.create_claim(db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/claims/policy/{policy_id}", response_model=List[schemas.InsuranceClaimRead])
def list_claims(
    policy_id: UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
    skip: int = 0,
    limit: int = 100,
):
    try:
        return service.list_claims_for_policy(db, policy_id=policy_id, skip=skip, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/claims/{claim_id}", response_model=schemas.InsuranceClaimRead)
def update_claim(
    claim_id: UUID,
    payload: schemas.InsuranceClaimUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    try:
        return service.update_claim(db, claim_id=claim_id, payload=payload)
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
