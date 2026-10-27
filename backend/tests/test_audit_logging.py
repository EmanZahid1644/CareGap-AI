
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.api import memberships as membership_api
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.audit import AuditLog
from backend.app.models.identity import (
    AccountType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    User,
)

client = TestClient(app)


# ============================================================
# HELPER: CREATE HOSPITAL TEST DATA
# ============================================================

def create_hospital_setup(db):
    organization = Organization(
        name="Audit Test Hospital",
        slug=f"audit-hospital-{uuid.uuid4().hex[:12]}",
        is_active=True,
    )
    db.add(organization)
    db.flush()

    owner = User(
        email=f"audit-owner-{uuid.uuid4().hex}@example.com",
        full_name="Audit Test Owner",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    clinician = User(
        email=f"audit-clinician-{uuid.uuid4().hex}@example.com",
        full_name="Audit Test Clinician",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    viewer = User(
        email=f"audit-viewer-{uuid.uuid4().hex}@example.com",
        full_name="Audit Test Viewer",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    db.add_all([owner, clinician, viewer])
    db.flush()

    owner_membership = OrganizationMembership(
        user_id=owner.id,
        organization_id=organization.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )

    clinician_membership = OrganizationMembership(
        user_id=clinician.id,
        organization_id=organization.id,
        role=OrganizationRole.CLINICIAN,
        is_active=True,
    )

    viewer_membership = OrganizationMembership(
        user_id=viewer.id,
        organization_id=organization.id,
        role=OrganizationRole.VIEWER,
        is_active=True,
    )

    db.add_all([
        owner_membership,
        clinician_membership,
        viewer_membership,
    ])
    db.flush()

    return {
        "organization": organization,
        "owner": owner,
        "clinician": clinician,
        "viewer": viewer,
        "owner_membership": owner_membership,
        "clinician_membership": clinician_membership,
        "viewer_membership": viewer_membership,
    }


def auth_headers(user):
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# TEST 1: STAFF CREATION AUDIT EVENT
# ============================================================

def test_staff_creation_generates_audit_event(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    new_staff = User(
        email=f"new-staff-{uuid.uuid4().hex}@example.com",
        full_name="New Audit Staff",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )
    isolated_db.add(new_staff)
    isolated_db.flush()

    response = client.post(
        f"/api/v1/organizations/{organization.id}/members",
        json={
            "user_id": str(new_staff.id),
            "role": "clinician",
        },
        headers=auth_headers(owner),
    )

    assert response.status_code == 201, response.text

    membership_id = uuid.UUID(response.json()["id"])

    events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.actor_user_id == owner.id,
            AuditLog.action == "membership.created",
            AuditLog.resource_id == membership_id,
        )
    ).all()

    assert len(events) == 1
    assert events[0].resource_type == "organization_membership"
    assert events[0].created_at is not None


# ============================================================
# TEST 2: ROLE UPDATE AUDIT EVENT
# ============================================================

def test_staff_role_update_generates_audit_event(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]
    clinician_membership = setup["clinician_membership"]

    response = client.patch(
        f"/api/v1/organizations/{organization.id}"
        f"/members/{clinician_membership.id}/role",
        json={"role": "reviewer"},
        headers=auth_headers(owner),
    )

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "reviewer"

    isolated_db.refresh(clinician_membership)
    assert clinician_membership.role == OrganizationRole.REVIEWER

    events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.actor_user_id == owner.id,
            AuditLog.action == "membership.role_updated",
            AuditLog.resource_id == clinician_membership.id,
        )
    ).all()

    assert len(events) == 1
    assert events[0].resource_type == "organization_membership"
    assert events[0].created_at is not None


# ============================================================
# TEST 3: DEACTIVATION AUDIT EVENT
# ============================================================

def test_staff_deactivation_generates_audit_event(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]
    clinician_membership = setup["clinician_membership"]

    response = client.patch(
        f"/api/v1/organizations/{organization.id}"
        f"/members/{clinician_membership.id}/deactivate",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_active"] is False

    isolated_db.refresh(clinician_membership)
    assert clinician_membership.is_active is False

    events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.actor_user_id == owner.id,
            AuditLog.action == "membership.deactivated",
            AuditLog.resource_id == clinician_membership.id,
        )
    ).all()

    assert len(events) == 1
    assert events[0].resource_type == "organization_membership"
    assert events[0].created_at is not None


# ============================================================
# TEST 4: UNAUTHORIZED ACTION CREATES NO AUDIT EVENT
# ============================================================

def test_unauthorized_role_update_creates_no_audit_event(
    isolated_db,
):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    viewer = setup["viewer"]
    clinician_membership = setup["clinician_membership"]

    response = client.patch(
        f"/api/v1/organizations/{organization.id}"
        f"/members/{clinician_membership.id}/role",
        json={"role": "admin"},
        headers=auth_headers(viewer),
    )

    assert response.status_code == 403

    isolated_db.refresh(clinician_membership)
    assert clinician_membership.role == OrganizationRole.CLINICIAN

    events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.action == "membership.role_updated",
            AuditLog.resource_id == clinician_membership.id,
        )
    ).all()

    assert len(events) == 0


# ============================================================
# TEST 5: AUDIT FAILURE MUST ROLL BACK ROLE UPDATE
# ============================================================

def test_role_update_rolls_back_when_audit_insert_fails(
    isolated_db,
    monkeypatch,
):
    setup = create_hospital_setup(isolated_db)

    organization_id = setup["organization"].id
    owner_id = setup["owner"].id
    membership_id = setup["clinician_membership"].id

    # Preserve setup in the fixture's outer transaction.
    isolated_db.commit()

    def failing_audit_event(db, **kwargs):
        raise IntegrityError(
            statement="simulated audit insert",
            params={},
            orig=Exception("Simulated audit failure"),
        )

    monkeypatch.setattr(
        membership_api,
        "record_audit_event",
        failing_audit_event,
    )

    token = create_access_token(subject=str(owner_id))

    with pytest.raises(IntegrityError):
        client.patch(
            f"/api/v1/organizations/{organization_id}"
            f"/members/{membership_id}/role",
            json={"role": "reviewer"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Roll back the failed request transaction.
    #isolated_db.rollback()
    isolated_db.expire_all()

    membership_after = isolated_db.get(
        OrganizationMembership,
        membership_id,
    )

    assert membership_after is not None
    assert membership_after.role == OrganizationRole.CLINICIAN

    events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization_id,
            AuditLog.action == "membership.role_updated",
            AuditLog.resource_id == membership_id,
        )
    ).all()

    assert len(events) == 0

def test_deactivation_rolls_back_when_audit_fails(
    isolated_db,
    monkeypatch,
):
    setup = create_hospital_setup(isolated_db)

    organization_id = setup["organization"].id
    owner_id = setup["owner"].id
    membership_id = setup["clinician_membership"].id

    # Preserve setup inside the test fixture's outer transaction.
    isolated_db.commit()

    def failing_audit_event(db, **kwargs):
        raise IntegrityError(
            statement="simulated deactivation audit failure",
            params={},
            orig=Exception("Simulated audit failure"),
        )

    monkeypatch.setattr(
        membership_api,
        "record_audit_event",
        failing_audit_event,
    )

    token = create_access_token(subject=str(owner_id))

    with pytest.raises(IntegrityError):
        client.patch(
            f"/api/v1/organizations/{organization_id}"
            f"/members/{membership_id}/deactivate",
            headers={"Authorization": f"Bearer {token}"},
        )

    # No manual rollback: endpoint must handle it.
    isolated_db.expire_all()

    membership_after = isolated_db.get(
        OrganizationMembership,
        membership_id,
    )

    assert membership_after is not None
    assert membership_after.is_active is True

    events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization_id,
            AuditLog.action == "membership.deactivated",
            AuditLog.resource_id == membership_id,
        )
    ).all()

    assert len(events) == 0

def test_staff_creation_rolls_back_when_audit_fails(
    isolated_db,
    monkeypatch,
):
    setup = create_hospital_setup(isolated_db)

    organization_id = setup["organization"].id
    owner_id = setup["owner"].id

    new_staff = User(
        email=f"rollback-staff-{uuid.uuid4().hex}@example.com",
        full_name="Rollback Staff",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add(new_staff)
    isolated_db.flush()

    new_staff_id = new_staff.id

    # Preserve test setup in the fixture's outer transaction.
    isolated_db.commit()

    def failing_audit_event(db, **kwargs):
        raise IntegrityError(
            statement="simulated staff creation audit failure",
            params={},
            orig=Exception("Simulated audit failure"),
        )

    monkeypatch.setattr(
        membership_api,
        "record_audit_event",
        failing_audit_event,
    )

    token = create_access_token(subject=str(owner_id))

    # The endpoint currently converts IntegrityError to HTTP 409.
    
    with pytest.raises(IntegrityError):
        client.post(
            f"/api/v1/organizations/{organization_id}/members",
            json={
                "user_id": str(new_staff_id),
                "role": "clinician",
            },
            headers={"Authorization": f"Bearer {token}"},
        )


    # No manual rollback: the endpoint must handle it.
    isolated_db.expire_all()

    membership = isolated_db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == new_staff_id,
        )
    )

    assert membership is None

    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization_id,
            AuditLog.action == "membership.created",
        )
    ).all()

    assert len(audit_events) == 0

def test_duplicate_membership_constraint_returns_409(
    isolated_db,
    monkeypatch,
):
    from unittest.mock import Mock

    setup = create_hospital_setup(isolated_db)

    organization_id = setup["organization"].id
    owner_id = setup["owner"].id

    new_staff = User(
        email=f"duplicate-staff-{uuid.uuid4().hex}@example.com",
        full_name="Duplicate Constraint Staff",
        password_hash="test-only-hash",
        account_type=AccountType.HOSPITAL,
        is_active=True,
    )

    isolated_db.add(new_staff)
    isolated_db.flush()

    new_staff_id = new_staff.id

    # Preserve setup in fixture's outer transaction.
    isolated_db.commit()

    def failing_flush(*args, **kwargs):
        original_error = Mock()
        original_error.sqlstate = "23505"
        original_error.diag.constraint_name = (
            "uq_membership_user_organization"
        )

        raise IntegrityError(
            statement="simulated duplicate membership insert",
            params={},
            orig=original_error,
        )

    monkeypatch.setattr(
        isolated_db,
        "flush",
        failing_flush,
    )

    token = create_access_token(subject=str(owner_id))

    response = client.post(
        f"/api/v1/organizations/{organization_id}/members",
        json={
            "user_id": str(new_staff_id),
            "role": "clinician",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "User already has a membership in this organization."
    )
