
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_user,
    get_organization_membership,
)
from backend.app.db.session import get_db
from backend.app.models.identity import (
    AccountType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    User,
)
from backend.app.schemas.organization import (
    OrganizationCreateRequest,
    OrganizationResponse,
)


router = APIRouter(
    prefix="/api/v1/organizations",
    tags=["Organizations"],
)


# ============================================================
# CREATE ORGANIZATION
# ============================================================

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    payload: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.account_type != AccountType.HOSPITAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital accounts can create organizations.",
        )

    existing_organization = db.scalar(
        select(Organization).where(
            Organization.slug == payload.slug
        )
    )

    if existing_organization is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug is already registered.",
        )

    organization = Organization(
        name=payload.name,
        slug=payload.slug,
        is_active=True,
    )

    db.add(organization)

    try:
        db.flush()

        membership = OrganizationMembership(
            user_id=current_user.id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
            is_active=True,
        )

        db.add(membership)

        # Organization and ownership are saved together.
        db.commit()
        db.refresh(organization)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization could not be created due to a conflict.",
        )

    return organization


# ============================================================
# LIST MY ORGANIZATIONS
# ============================================================

@router.get(
    "",
    response_model=list[OrganizationResponse],
    status_code=status.HTTP_200_OK,
)
def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = (
        select(Organization)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id
            == Organization.id,
        )
        .where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.is_active.is_(True),
            Organization.is_active.is_(True),
        )
        .order_by(Organization.name, Organization.id)
    )

    organizations = db.scalars(statement).all()

    return organizations


# ============================================================
# GET ORGANIZATION DETAILS
# ============================================================

@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
)
def get_organization_details(
    organization_id: UUID,
    membership: OrganizationMembership = Depends(
        get_organization_membership
    ),
    db: Session = Depends(get_db),
):
    # The dependency has already verified that the current
    # user has an active membership in this active organization.
    organization = db.get(
        Organization,
        membership.organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    return organization
