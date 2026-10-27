
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
def role_setup(isolated_db):
    organization = Organization(
        name="Role Security Hospital",
        slug=f"role-security-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add(organization)
    isolated_db.flush()

    def add_member(role):
        user = User(
            email=f"role-{uuid.uuid4().hex}@example.com",
            full_name="Role Test User",
            password_hash="test-only-hash",
            account_type=AccountType.HOSPITAL,
            is_active=True,
        )

        isolated_db.add(user)
        isolated_db.flush()

        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=organization.id,
            role=role,
            is_active=True,
        )

        isolated_db.add(membership)
        isolated_db.flush()

        token = create_access_token(subject=str(user.id))

        return {
            "user": user,
            "membership": membership,
            "headers": {
                "Authorization": f"Bearer {token}",
            },
        }

    return {
        "organization": organization,
        "add_member": add_member,
    }


def patch_role(setup, actor, target, role):
    organization_id = setup["organization"].id
    membership_id = target["membership"].id

    return client.patch(
        f"/api/v1/organizations/{organization_id}"
        f"/members/{membership_id}/role",
        json={"role": role},
        headers=actor["headers"],
    )


def test_owner_can_update_clinician_role(role_setup):
    owner = role_setup["add_member"](OrganizationRole.OWNER)
    clinician = role_setup["add_member"](
        OrganizationRole.CLINICIAN
    )

    response = patch_role(
        role_setup, owner, clinician, "reviewer"
    )

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "reviewer"


def test_admin_can_update_viewer_role(role_setup):
    admin = role_setup["add_member"](OrganizationRole.ADMIN)
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)

    response = patch_role(
        role_setup, admin, viewer, "clinician"
    )

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "clinician"


def test_viewer_cannot_update_roles(role_setup):
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)
    clinician = role_setup["add_member"](
        OrganizationRole.CLINICIAN
    )

    response = patch_role(
        role_setup, viewer, clinician, "reviewer"
    )

    assert response.status_code == 403


def test_owner_role_cannot_be_modified(role_setup):
    owner = role_setup["add_member"](OrganizationRole.OWNER)

    response = patch_role(
        role_setup, owner, owner, "admin"
    )

    assert response.status_code == 403


def test_cannot_promote_member_to_owner(role_setup):
    owner = role_setup["add_member"](OrganizationRole.OWNER)
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)

    response = patch_role(
        role_setup, owner, viewer, "owner"
    )

    assert response.status_code == 403


def test_admin_cannot_promote_to_admin(role_setup):
    admin = role_setup["add_member"](OrganizationRole.ADMIN)
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)

    response = patch_role(
        role_setup, admin, viewer, "admin"
    )

    assert response.status_code == 403


def test_admin_cannot_modify_another_admin(role_setup):
    admin_a = role_setup["add_member"](OrganizationRole.ADMIN)
    admin_b = role_setup["add_member"](OrganizationRole.ADMIN)

    response = patch_role(
        role_setup, admin_a, admin_b, "viewer"
    )

    assert response.status_code == 403


def test_admin_cannot_change_own_role(role_setup):
    admin = role_setup["add_member"](OrganizationRole.ADMIN)

    response = patch_role(
        role_setup, admin, admin, "viewer"
    )

    assert response.status_code == 403



def test_inactive_membership_cannot_be_updated(
    role_setup,
    isolated_db,
):
    owner = role_setup["add_member"](OrganizationRole.OWNER)
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)

    # Mark the membership inactive.
    viewer["membership"].is_active = False

    # Persist the change inside the test transaction.
    isolated_db.flush()

    response = patch_role(
        role_setup,
        owner,
        viewer,
        "clinician",
    )

    assert response.status_code == 404, response.text

    # Confirm the membership was not reactivated.
    isolated_db.refresh(viewer["membership"])

    assert viewer["membership"].is_active is False
    assert viewer["membership"].role == OrganizationRole.VIEWER


    assert response.status_code == 404


def test_other_hospital_membership_cannot_be_updated(
    role_setup,
    isolated_db,
):
    owner = role_setup["add_member"](OrganizationRole.OWNER)

    other_hospital = Organization(
        name="Other Role Hospital",
        slug=f"other-role-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add(other_hospital)
    isolated_db.flush()

    other_user = User(
        email=f"other-role-{uuid.uuid4().hex}@example.com",
        full_name="Other Hospital User",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add(other_user)
    isolated_db.flush()

    other_membership = OrganizationMembership(
        user_id=other_user.id,
        organization_id=other_hospital.id,
        role=OrganizationRole.VIEWER,
        is_active=True,
    )

    isolated_db.add(other_membership)
    isolated_db.flush()

    response = client.patch(
        f"/api/v1/organizations/"
        f"{role_setup['organization'].id}"
        f"/members/{other_membership.id}/role",
        json={"role": "clinician"},
        headers=owner["headers"],
    )

    assert response.status_code == 404
    assert other_membership.role == OrganizationRole.VIEWER

def deactivate_member(setup, actor, target):
    organization_id = setup["organization"].id
    membership_id = target["membership"].id

    return client.patch(
        f"/api/v1/organizations/{organization_id}"
        f"/members/{membership_id}/deactivate",
        headers=actor["headers"],
    )


def test_owner_can_deactivate_clinician(
    role_setup,
    isolated_db,
):
    owner = role_setup["add_member"](OrganizationRole.OWNER)
    clinician = role_setup["add_member"](
        OrganizationRole.CLINICIAN
    )

    response = deactivate_member(role_setup, owner, clinician)

    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is False

    isolated_db.refresh(clinician["membership"])
    assert clinician["membership"].is_active is False


def test_admin_can_deactivate_viewer(role_setup):
    admin = role_setup["add_member"](OrganizationRole.ADMIN)
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)

    response = deactivate_member(role_setup, admin, viewer)

    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is False


def test_viewer_cannot_deactivate_staff(role_setup):
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)
    clinician = role_setup["add_member"](
        OrganizationRole.CLINICIAN
    )

    response = deactivate_member(role_setup, viewer, clinician)

    assert response.status_code == 403


def test_owner_cannot_be_deactivated(role_setup):
    owner = role_setup["add_member"](OrganizationRole.OWNER)

    response = deactivate_member(role_setup, owner, owner)

    assert response.status_code == 403


def test_admin_cannot_deactivate_another_admin(role_setup):
    admin_a = role_setup["add_member"](OrganizationRole.ADMIN)
    admin_b = role_setup["add_member"](OrganizationRole.ADMIN)

    response = deactivate_member(role_setup, admin_a, admin_b)

    assert response.status_code == 403


def test_admin_cannot_deactivate_self(role_setup):
    admin = role_setup["add_member"](OrganizationRole.ADMIN)

    response = deactivate_member(role_setup, admin, admin)

    assert response.status_code == 403


def test_already_inactive_membership_returns_conflict(
    role_setup,
    isolated_db,
):
    owner = role_setup["add_member"](OrganizationRole.OWNER)
    viewer = role_setup["add_member"](OrganizationRole.VIEWER)

    viewer["membership"].is_active = False
    isolated_db.flush()

    response = deactivate_member(role_setup, owner, viewer)

    assert response.status_code == 409


def test_deactivation_cannot_cross_hospitals(
    role_setup,
    isolated_db,
):
    owner = role_setup["add_member"](OrganizationRole.OWNER)

    other_hospital = Organization(
        name="Other Deactivation Hospital",
        slug=f"deactivate-other-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )

    isolated_db.add(other_hospital)
    isolated_db.flush()

    other_user = User(
        email=f"deactivate-other-{uuid.uuid4().hex}@example.com",
        full_name="Other Hospital Staff",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add(other_user)
    isolated_db.flush()

    other_membership = OrganizationMembership(
        user_id=other_user.id,
        organization_id=other_hospital.id,
        role=OrganizationRole.VIEWER,
        is_active=True,
    )

    isolated_db.add(other_membership)
    isolated_db.flush()

    response = client.patch(
        f"/api/v1/organizations/{role_setup['organization'].id}"
        f"/members/{other_membership.id}/deactivate",
        headers=owner["headers"],
    )

    assert response.status_code == 404

    isolated_db.refresh(other_membership)
    assert other_membership.is_active is True

def test_deactivated_staff_loses_hospital_access(
    role_setup,
):
    owner = role_setup["add_member"](
        OrganizationRole.OWNER
    )

    clinician = role_setup["add_member"](
        OrganizationRole.CLINICIAN
    )

    organization_id = role_setup["organization"].id

    # Before deactivation: clinician can access staff listing.
    before_response = client.get(
        f"/api/v1/organizations/{organization_id}/members",
        headers=clinician["headers"],
    )

    assert before_response.status_code == 200

    # Owner deactivates clinician.
    deactivate_response = deactivate_member(
        role_setup,
        owner,
        clinician,
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    # Same JWT must no longer provide hospital access.
    after_response = client.get(
        f"/api/v1/organizations/{organization_id}/members",
        headers=clinician["headers"],
    )

    assert after_response.status_code == 404

    # Deactivated clinician cannot update roles either.
    update_response = patch_role(
        role_setup,
        clinician,
        owner,
        "viewer",
    )

    assert update_response.status_code == 404
