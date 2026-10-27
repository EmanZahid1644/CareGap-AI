
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
from backend.app.models.identity import (
    AccountType,
    OrganizationMembership,
    OrganizationRole,
    User,
)
from backend.app.schemas.membership import (
    MembershipCreateRequest,
    MembershipResponse,
    MembershipRoleUpdateRequest,
)
from backend.app.services.audit import (
    AuditAction,
    record_audit_event,
)


router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/members",
    tags=["Organization Members"],
)


# ============================================================
# 1. ADD HOSPITAL STAFF MEMBER
# ============================================================


@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_organization_member(
    organization_id: UUID,
    payload: MembershipCreateRequest,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.STAFF_MANAGE)
    ),
    db: Session = Depends(get_db),
):
    # OWNER role cannot be assigned through this endpoint.
    if payload.role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=403,
            detail="Owner role cannot be assigned through this endpoint.",
        )

    # Target user must be an active hospital account.
    target_user = db.get(User, payload.user_id)

    if (
        target_user is None
        or not target_user.is_active
        or target_user.account_type != AccountType.HOSPITAL
    ):
        raise HTTPException(
            status_code=404,
            detail="Eligible hospital user not found.",
        )

    # Prevent duplicate organization memberships.
    existing_membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id
            == acting_membership.organization_id,
            OrganizationMembership.user_id == target_user.id,
        )
    )

    if existing_membership is not None:
        raise HTTPException(
            status_code=409,
            detail="User already has a membership in this organization.",
        )

    membership = OrganizationMembership(
        organization_id=acting_membership.organization_id,
        user_id=target_user.id,
        role=payload.role,
        is_active=True,
    )

    try:
        db.add(membership)

        # Insert membership and generate its UUID.
        db.flush()

        # Record staff creation in the same transaction.
        record_audit_event(
            db,
            organization_id=acting_membership.organization_id,
            actor_user_id=acting_membership.user_id,
            action=AuditAction.MEMBERSHIP_CREATED,
            resource_type="organization_membership",
            resource_id=membership.id,
        )

        # Commit membership and audit event atomically.
        db.commit()

    
    except IntegrityError as exc:
        db.rollback()

        # PostgreSQL unique-constraint violation.
        sqlstate = getattr(exc.orig, "sqlstate", None)
        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if (
            sqlstate == "23505"
            and constraint_name == "uq_membership_user_organization"
        ):
            raise HTTPException(
                status_code=409,
                detail="User already has a membership in this organization.",
            ) from exc

        # All other integrity failures are unexpected.
        raise

    except Exception:
        db.rollback()
        raise


    db.refresh(membership)
    return membership


# ============================================================
# 2. LIST HOSPITAL STAFF MEMBERS
# ============================================================

@router.get(
    "",
    response_model=list[MembershipResponse],
    status_code=status.HTTP_200_OK,
)
def list_organization_members(
    organization_id: UUID,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.STAFF_READ)
    ),
    db: Session = Depends(get_db),
):
    statement = (
        select(OrganizationMembership)
        .where(
            OrganizationMembership.organization_id
            == acting_membership.organization_id
        )
        .order_by(
            OrganizationMembership.created_at,
            OrganizationMembership.id,
        )
    )

    return db.scalars(statement).all()


# ============================================================
# 3. UPDATE HOSPITAL STAFF ROLE
# ============================================================

@router.patch(
    "/{membership_id}/role",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
)
def update_organization_member_role(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipRoleUpdateRequest,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.STAFF_MANAGE)
    ),
    db: Session = Depends(get_db),
):
    target_membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.id == membership_id,
            OrganizationMembership.organization_id
            == acting_membership.organization_id,
            OrganizationMembership.is_active.is_(True),
        )
    )

    if target_membership is None:
        raise HTTPException(
            status_code=404,
            detail="Active organization membership not found.",
        )

    # OWNER role is protected.
    if (
        target_membership.role == OrganizationRole.OWNER
        or payload.role == OrganizationRole.OWNER
    ):
        raise HTTPException(
            status_code=403,
            detail="Owner role cannot be modified through this endpoint.",
        )

    # ADMIN cannot modify their own role.
    if (
        acting_membership.role == OrganizationRole.ADMIN
        and target_membership.id == acting_membership.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Administrators cannot change their own role.",
        )

    # Only OWNER can manage ADMIN roles.
    if (
        acting_membership.role == OrganizationRole.ADMIN
        and (
            target_membership.role == OrganizationRole.ADMIN
            or payload.role == OrganizationRole.ADMIN
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Only organization owners can manage administrator roles.",
        )

    
    # Update staff role.
   
    try:
        target_membership.role = payload.role

        record_audit_event(
            db,
            organization_id=acting_membership.organization_id,
            actor_user_id=acting_membership.user_id,
            action=AuditAction.MEMBERSHIP_ROLE_UPDATED,
            resource_type="organization_membership",
            resource_id=target_membership.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(target_membership)
    return target_membership


# ============================================================
# 4. DEACTIVATE HOSPITAL STAFF MEMBER
# ============================================================

@router.patch(
    "/{membership_id}/deactivate",
    response_model=MembershipResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_organization_member(
    organization_id: UUID,
    membership_id: UUID,
    acting_membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.STAFF_MANAGE)
    ),
    db: Session = Depends(get_db),
):
    target_membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.id == membership_id,
            OrganizationMembership.organization_id
            == acting_membership.organization_id,
        )
    )

    if target_membership is None:
        raise HTTPException(
            status_code=404,
            detail="Organization membership not found.",
        )

    if not target_membership.is_active:
        raise HTTPException(
            status_code=409,
            detail="Organization membership is already inactive.",
        )

    # OWNER cannot be deactivated through this endpoint.
    if target_membership.role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=403,
            detail="Organization owners cannot be deactivated here.",
        )

    # ADMIN cannot deactivate themselves or another ADMIN.
    if acting_membership.role == OrganizationRole.ADMIN:
        if target_membership.id == acting_membership.id:
            raise HTTPException(
                status_code=403,
                detail="Administrators cannot deactivate themselves.",
            )

        if target_membership.role == OrganizationRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Only owners can deactivate administrators.",
            )

    # Soft deactivation preserves membership history.
   
    # Soft deactivate the hospital membership.
    
    try:
        target_membership.is_active = False

        record_audit_event(
            db,
            organization_id=acting_membership.organization_id,
            actor_user_id=acting_membership.user_id,
            action=AuditAction.MEMBERSHIP_DEACTIVATED,
            resource_type="organization_membership",
            resource_id=target_membership.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(target_membership)
    return target_membership
