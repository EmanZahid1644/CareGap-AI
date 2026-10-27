
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.identity import (
    AccountType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    User,
)


client = TestClient(app)


@pytest.fixture
def hospital_user(isolated_db):
    user = User(
        email=f"hospital-{uuid.uuid4().hex}@example.com",
        full_name="Hospital Test Owner",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add(user)
    isolated_db.flush()

    token = create_access_token(subject=str(user.id))

    return {
        "user": user,
        "headers": {
            "Authorization": f"Bearer {token}",
        },
    }


def test_create_organization_success(
    hospital_user,
    isolated_db,
):
    slug = f"hospital-{uuid.uuid4().hex[:12]}"

    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "Test General Hospital",
            "slug": slug,
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test General Hospital"
    assert data["slug"] == slug
    assert data["is_active"] is True

    organization = isolated_db.get(
        Organization,
        uuid.UUID(data["id"]),
    )

    assert organization is not None

    membership = isolated_db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id
            == organization.id,
            OrganizationMembership.user_id
            == hospital_user["user"].id,
        )
    )

    assert membership is not None
    assert membership.role == OrganizationRole.OWNER
    assert membership.is_active is True


def test_duplicate_organization_slug(
    hospital_user,
):
    slug = f"duplicate-hospital-{uuid.uuid4().hex[:12]}"

    payload = {
        "name": "Duplicate Hospital",
        "slug": slug,
    }

    first_response = client.post(
        "/api/v1/organizations",
        json=payload,
        headers=hospital_user["headers"],
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/organizations",
        json=payload,
        headers=hospital_user["headers"],
    )

    assert second_response.status_code == 409


def test_personal_account_cannot_create_organization(
    isolated_db,
):
    user = User(
        email=f"personal-{uuid.uuid4().hex}@example.com",
        full_name="Personal Test User",
        password_hash="test-only-hash",
        account_type=AccountType.PERSONAL,
        is_active=True,
    )

    isolated_db.add(user)
    isolated_db.flush()

    token = create_access_token(subject=str(user.id))

    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "Unauthorized Hospital",
            "slug": f"unauthorized-{uuid.uuid4().hex[:12]}",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_unauthenticated_organization_creation():
    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "Unauthenticated Hospital",
            "slug": "unauthenticated-hospital",
        },
    )

    assert response.status_code == 401


def test_invalid_organization_slug(
    hospital_user,
):
    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "Invalid Slug Hospital",
            "slug": "Invalid Slug!",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 422
def test_list_my_organizations(
    hospital_user,
    isolated_db,
):
    suffix = uuid.uuid4().hex[:12]

    hospital_a = Organization(
        name="Hospital A",
        slug=f"hospital-a-{suffix}",
        is_active=True,
    )

    hospital_b = Organization(
        name="Hospital B",
        slug=f"hospital-b-{suffix}",
        is_active=True,
    )

    isolated_db.add_all([hospital_a, hospital_b])
    isolated_db.flush()

    membership = OrganizationMembership(
        user_id=hospital_user["user"].id,
        organization_id=hospital_a.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )

    isolated_db.add(membership)
    isolated_db.flush()

    response = client.get(
        "/api/v1/organizations",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(hospital_a.id)
    assert data[0]["name"] == "Hospital A"


def test_get_my_organization_details(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="My Hospital",
        slug=f"my-hospital-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add(organization)
    isolated_db.flush()

    membership = OrganizationMembership(
        user_id=hospital_user["user"].id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )

    isolated_db.add(membership)
    isolated_db.flush()

    response = client.get(
        f"/api/v1/organizations/{organization.id}",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(organization.id)


def test_cannot_get_other_hospital_details(
    hospital_user,
    isolated_db,
):
    other_hospital = Organization(
        name="Other Hospital",
        slug=f"other-hospital-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add(other_hospital)
    isolated_db.flush()

    response = client.get(
        f"/api/v1/organizations/{other_hospital.id}",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 404


def test_inactive_membership_excluded_from_list(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Inactive Membership Hospital",
        slug=f"inactive-member-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add(organization)
    isolated_db.flush()

    membership = OrganizationMembership(
        user_id=hospital_user["user"].id,
        organization_id=organization.id,
        role=OrganizationRole.VIEWER,
        is_active=False,
    )

    isolated_db.add(membership)
    isolated_db.flush()

    response = client.get(
        "/api/v1/organizations",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 200
    assert response.json() == []


def test_inactive_hospital_excluded_from_list(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Inactive Hospital",
        slug=f"inactive-hospital-{uuid.uuid4().hex[:12]}",
        is_active=False,
    )

    isolated_db.add(organization)
    isolated_db.flush()

    membership = OrganizationMembership(
        user_id=hospital_user["user"].id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )

    isolated_db.add(membership)
    isolated_db.flush()

    response = client.get(
        "/api/v1/organizations",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 200
    assert response.json() == []

def test_owner_can_add_hospital_staff(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Staff Test Hospital",
        slug=f"staff-test-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    target_user = User(
        email=f"clinician-{uuid.uuid4().hex}@example.com",
        full_name="Test Clinician",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([organization, target_user])
    isolated_db.flush()

    owner_membership = OrganizationMembership(
        user_id=hospital_user["user"].id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )

    isolated_db.add(owner_membership)
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(target_user.id),
            "role": "clinician",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["user_id"] == str(target_user.id)
    assert data["organization_id"] == str(organization.id)
    assert data["role"] == "clinician"
    assert data["is_active"] is True


def test_owner_cannot_assign_owner_role_through_staff_api(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Owner Protection Hospital",
        slug=f"owner-protection-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    target_user = User(
        email=f"new-owner-{uuid.uuid4().hex}@example.com",
        full_name="New Owner Candidate",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([organization, target_user])
    isolated_db.flush()

    isolated_db.add(
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
            is_active=True,
        )
    )
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(target_user.id),
            "role": "owner",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 403


def test_duplicate_staff_membership_rejected(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Duplicate Staff Hospital",
        slug=f"duplicate-staff-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    target_user = User(
        email=f"duplicate-{uuid.uuid4().hex}@example.com",
        full_name="Existing Staff",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([organization, target_user])
    isolated_db.flush()

    isolated_db.add_all([
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
            is_active=True,
        ),
        OrganizationMembership(
            user_id=target_user.id,
            organization_id=organization.id,
            role=OrganizationRole.VIEWER,
            is_active=True,
        ),
    ])
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(target_user.id),
            "role": "clinician",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 409


def test_personal_account_cannot_be_added_as_staff(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Personal Account Protection",
        slug=f"personal-protection-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    personal_user = User(
        email=f"personal-staff-{uuid.uuid4().hex}@example.com",
        full_name="Personal User",
        password_hash="test-only-hash",
        account_type=AccountType.PERSONAL,
        is_active=True,
    )

    isolated_db.add_all([organization, personal_user])
    isolated_db.flush()

    isolated_db.add(
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
            is_active=True,
        )
    )
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(personal_user.id),
            "role": "viewer",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 404

@pytest.mark.parametrize(
    "acting_role,expected_status",
    [
        (OrganizationRole.ADMIN, 201),
        (OrganizationRole.VIEWER, 403),
        (OrganizationRole.CLINICIAN, 403),
    ],
)
def test_staff_creation_respects_role_permissions(
    hospital_user,
    isolated_db,
    acting_role,
    expected_status,
):
    organization = Organization(
        name="Role Permission Hospital",
        slug=f"role-permission-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    target_user = User(
        email=f"role-target-{uuid.uuid4().hex}@example.com",
        full_name="Role Target",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([organization, target_user])
    isolated_db.flush()

    isolated_db.add(
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=organization.id,
            role=acting_role,
            is_active=True,
        )
    )
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(target_user.id),
            "role": "viewer",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == expected_status, response.text


def test_admin_cannot_assign_owner_role(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Admin Owner Protection",
        slug=f"admin-owner-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    target_user = User(
        email=f"admin-target-{uuid.uuid4().hex}@example.com",
        full_name="Admin Target",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([organization, target_user])
    isolated_db.flush()

    isolated_db.add(
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=organization.id,
            role=OrganizationRole.ADMIN,
            is_active=True,
        )
    )
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(target_user.id),
            "role": "owner",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 403


def test_other_hospital_cannot_add_staff(
    hospital_user,
    isolated_db,
):
    hospital_a = Organization(
        name="Hospital A",
        slug=f"staff-a-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    hospital_b = Organization(
        name="Hospital B",
        slug=f"staff-b-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    target_user = User(
        email=f"cross-hospital-{uuid.uuid4().hex}@example.com",
        full_name="Cross Hospital Target",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([hospital_a, hospital_b, target_user])
    isolated_db.flush()

    isolated_db.add(
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=hospital_a.id,
            role=OrganizationRole.OWNER,
            is_active=True,
        )
    )
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{hospital_b.id}/members",
        json={
            "user_id": str(target_user.id),
            "role": "viewer",
        },
        headers=hospital_user["headers"],
    )

    assert response.status_code == 404

    membership = isolated_db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == hospital_b.id,
            OrganizationMembership.user_id == target_user.id,
        )
    )

    assert membership is None

def test_hospital_member_can_list_staff(
    hospital_user,
    isolated_db,
):
    organization = Organization(
        name="Staff Listing Hospital",
        slug=f"staff-list-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    staff_user = User(
        email=f"listing-staff-{uuid.uuid4().hex}@example.com",
        full_name="Listing Test Staff",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add_all([organization, staff_user])
    isolated_db.flush()

    isolated_db.add_all([
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=organization.id,
            role=OrganizationRole.VIEWER,
            is_active=True,
        ),
        OrganizationMembership(
            user_id=staff_user.id,
            organization_id=organization.id,
            role=OrganizationRole.CLINICIAN,
            is_active=True,
        ),
    ])
    isolated_db.flush()

    response = client.get(
        f"/api/v1/organizations/{organization.id}/members",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 2
    assert {member["user_id"] for member in data} == {
        str(hospital_user["user"].id),
        str(staff_user.id),
    }


def test_cannot_list_other_hospital_staff(
    hospital_user,
    isolated_db,
):
    hospital_a = Organization(
        name="Staff List Hospital A",
        slug=f"list-a-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    hospital_b = Organization(
        name="Staff List Hospital B",
        slug=f"list-b-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add_all([hospital_a, hospital_b])
    isolated_db.flush()

    isolated_db.add(
        OrganizationMembership(
            user_id=hospital_user["user"].id,
            organization_id=hospital_a.id,
            role=OrganizationRole.OWNER,
            is_active=True,
        )
    )
    isolated_db.flush()

    response = client.get(
        f"/api/v1/organizations/{hospital_b.id}/members",
        headers=hospital_user["headers"],
    )

    assert response.status_code == 404


def test_staff_listing_requires_authentication(
    isolated_db,
):
    response = client.get(
        f"/api/v1/organizations/{uuid.uuid4()}/members"
    )

    assert response.status_code == 401
