
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from backend.app.db.session import get_db
from backend.app.models.identity import OrganizationMembership
from backend.app.models.patient import Patient
from backend.app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from backend.app.services.audit import (
    AuditAction,
    record_audit_event,
)


router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/patients",
    tags=["Patients"],
)


# ============================================================
# 1. CREATE PATIENT
# ============================================================

@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(
    organization_id: UUID,
    payload: PatientCreate,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.CLINICAL_WRITE)
    ),
    db: Session = Depends(get_db),
):
    scoped_organization_id = acting_membership.organization_id

    existing_patient = db.scalar(
        select(Patient).where(
            Patient.organization_id == scoped_organization_id,
            Patient.patient_number == payload.patient_number,
        )
    )

    if existing_patient is not None:
        raise HTTPException(
            status_code=409,
            detail="Patient number already exists in this organization.",
        )

    patient = Patient(
        organization_id=scoped_organization_id,
        patient_number=payload.patient_number,
        full_name=payload.full_name,
        date_of_birth=payload.date_of_birth,
        sex_at_birth=payload.sex_at_birth,
        is_active=True,
    )

    try:
        db.add(patient)
        db.flush()

        record_audit_event(
            db,
            organization_id=scoped_organization_id,
            actor_user_id=acting_membership.user_id,
            action=AuditAction.PATIENT_CREATED,
            resource_type="patient",
            resource_id=patient.id,
        )

        db.commit()

    except IntegrityError as exc:
        db.rollback()

        sqlstate = getattr(exc.orig, "sqlstate", None)
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if (
            sqlstate == "23505"
            and constraint_name == "uq_patient_organization_number"
        ):
            raise HTTPException(
                status_code=409,
                detail="Patient number already exists in this organization.",
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise

    db.refresh(patient)
    return patient


# ============================================================
# 2. LIST PATIENTS
# ============================================================

@router.get(
    "",
    response_model=list[PatientResponse],
    status_code=status.HTTP_200_OK,
)
def list_patients(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 50,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.CLINICAL_READ)
    ),
    db: Session = Depends(get_db),
):
    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="Invalid pagination parameters.",
        )

    statement = (
        select(Patient)
        .where(
            Patient.organization_id
            == acting_membership.organization_id,
            Patient.is_active.is_(True),
        )
        .order_by(
            Patient.created_at,
            Patient.id,
        )
        .offset(skip)
        .limit(limit)
    )

    return db.scalars(statement).all()


# ============================================================
# 3. GET PATIENT DETAILS
# ============================================================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
)
def get_patient_details(
    organization_id: UUID,
    patient_id: UUID,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.CLINICAL_READ)
    ),
    db: Session = Depends(get_db),
):
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.organization_id
            == acting_membership.organization_id,
            Patient.is_active.is_(True),
        )
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    return patient


# ============================================================
# 4. UPDATE PATIENT
# ============================================================

@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
)
def update_patient(
    organization_id: UUID,
    patient_id: UUID,
    payload: PatientUpdate,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.CLINICAL_WRITE)
    ),
    db: Session = Depends(get_db),
):
    # Only access patients belonging to this organization.
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.organization_id
            == acting_membership.organization_id,
            Patient.is_active.is_(True),
        )
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # Only update fields explicitly included in the request.
    updates = payload.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided.",
        )

    # Full name is mandatory and cannot be cleared.
    if "full_name" in updates and updates["full_name"] is None:
        raise HTTPException(
            status_code=422,
            detail="Full name cannot be null.",
        )

    try:
        for field, value in updates.items():
            setattr(patient, field, value)

        db.flush()

        # Save audit event in the same database transaction.
        record_audit_event(
            db,
            organization_id=acting_membership.organization_id,
            actor_user_id=acting_membership.user_id,
            action=AuditAction.PATIENT_UPDATED,
            resource_type="patient",
            resource_id=patient.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(patient)
    return patient

# ============================================================
# 5. DEACTIVATE PATIENT
# ============================================================

@router.patch(
    "/{patient_id}/deactivate",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_patient(
    organization_id: UUID,
    patient_id: UUID,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.CLINICAL_WRITE)
    ),
    db: Session = Depends(get_db),
):
    # Only active patients from this organization are eligible.
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.organization_id
            == acting_membership.organization_id,
            Patient.is_active.is_(True),
        )
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    try:
        # Soft deactivation: preserve the database record.
        patient.is_active = False
        db.flush()

        # Audit event is saved in the same transaction.
        record_audit_event(
            db,
            organization_id=acting_membership.organization_id,
            actor_user_id=acting_membership.user_id,
            action=AuditAction.PATIENT_DEACTIVATED,
            resource_type="patient",
            resource_id=patient.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(patient)
    return patient
