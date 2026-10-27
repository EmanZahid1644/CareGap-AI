
import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.app.core.dependencies import (
    get_current_user,
    get_organization_membership,
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from backend.app.core.security import create_access_token
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.identity import (
    AccountType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    User,
)


# These routes exist only during testing.
# They exercise the real authorization dependencies.
authorization_app = FastAPI()

authorization_app.dependency_overrides = app.dependency_overrides


@authorization_app.get("/test/organizations/{organization_id}/membership")
def check_membership(
    membership: OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    return {
        "organization_id": str(membership.organization_id),
        "role": membership.role.value,
    }


@authorization_app.get("/test/organizations/{organization_id}/manage-staff")
def check_staff_management(
    membership: OrganizationMembership = Depends(
        require_organization_permission(Permission.STAFF_MANAGE)
    ),
):
    return {
        "authorized": True,
        "role": membership.role.value,
    }



client = TestClient(authorization_app)


@pytest.fixture
def hospital_data(isolated_db):
    suffix = uuid.uuid4().hex[:12]

    user = User(
        email=f"hospital-test-{suffix}@example.com",
        full_name="Hospital Authorization Test User",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

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

    isolated_db.add_all([user, hospital_a, hospital_b])
    isolated_db.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=hospital_a.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )

    isolated_db.add(membership)
    isolated_db.flush()

    token = create_access_token(subject=str(user.id))

    return {
        "user": user,
        "hospital_a": hospital_a,
        "hospital_b": hospital_b,
        "membership": membership,
        "headers": {
            "Authorization": f"Bearer {token}",
        },
    }


def test_hospital_a_member_can_access_hospital_a(hospital_data):
    hospital_a = hospital_data["hospital_a"]

    response = client.get(
        f"/test/organizations/{hospital_a.id}/membership",
        headers=hospital_data["headers"],
    )

    assert response.status_code == 200
    assert response.json()["organization_id"] == str(hospital_a.id)
    assert response.json()["role"] == "owner"


def test_hospital_a_member_cannot_access_hospital_b(hospital_data):
    hospital_b = hospital_data["hospital_b"]

    response = client.get(
        f"/test/organizations/{hospital_b.id}/membership",
        headers=hospital_data["headers"],
    )

    assert response.status_code == 404


def test_inactive_membership_is_rejected(
    hospital_data,
    isolated_db,
):
    membership = hospital_data["membership"]
    membership.is_active = False
    isolated_db.flush()

    hospital_a = hospital_data["hospital_a"]

    response = client.get(
        f"/test/organizations/{hospital_a.id}/membership",
        headers=hospital_data["headers"],
    )

    assert response.status_code == 404


def test_inactive_hospital_is_rejected(
    hospital_data,
    isolated_db,
):
    hospital_a = hospital_data["hospital_a"]
    hospital_a.is_active = False
    isolated_db.flush()

    response = client.get(
        f"/test/organizations/{hospital_a.id}/membership",
        headers=hospital_data["headers"],
    )

    assert response.status_code == 404


def test_owner_can_manage_staff(hospital_data):
    hospital_a = hospital_data["hospital_a"]

    response = client.get(
        f"/test/organizations/{hospital_a.id}/manage-staff",
        headers=hospital_data["headers"],
    )

    assert response.status_code == 200
    assert response.json()["authorized"] is True


def test_viewer_cannot_manage_staff(
    hospital_data,
    isolated_db,
):
    membership = hospital_data["membership"]
    membership.role = OrganizationRole.VIEWER
    isolated_db.flush()

    hospital_a = hospital_data["hospital_a"]

    response = client.get(
        f"/test/organizations/{hospital_a.id}/manage-staff",
        headers=hospital_data["headers"],
    )

    assert response.status_code == 403


def test_unauthenticated_hospital_access_is_rejected(hospital_data):
    hospital_a = hospital_data["hospital_a"]

    response = client.get(
        f"/test/organizations/{hospital_a.id}/membership"
    )

    assert response.status_code == 401

