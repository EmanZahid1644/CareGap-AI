
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.audit import AuditLog
from backend.app.models.patient import Patient
from backend.app.services.audit import AuditAction

from backend.tests.test_audit_logging import create_hospital_setup
import pytest

client = TestClient(app)


def test_clinician_can_register_patient_with_audit_event(isolated_db):
    # Arrange: Create synthetic hospital and staff.
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    clinician = setup["clinician"]

    token = create_access_token(subject=str(clinician.id))

    # Act: Register a synthetic patient.
    response = client.post(
        f"/api/v1/organizations/{organization.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "patient_number": "PAT-001",
            "full_name": "Synthetic Test Patient",
            "date_of_birth": "1998-04-12",
            "sex_at_birth": "female",
        },
    )

    # Assert: API responds with 201 Created.
    assert response.status_code == 201, response.text

    data = response.json()

    assert data["patient_number"] == "PAT-001"
    assert data["full_name"] == "Synthetic Test Patient"
    assert data["organization_id"] == str(organization.id)
    assert data["sex_at_birth"] == "female"
    assert data["is_active"] is True

    # Verify patient was persisted in the test transaction.
    patient = isolated_db.scalar(
        select(Patient).where(
            Patient.organization_id == organization.id,
            Patient.patient_number == "PAT-001",
        )
    )

    assert patient is not None
    assert str(patient.id) == data["id"]

    # Verify the audit event was saved.
    audit_event = isolated_db.scalar(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.resource_type == "patient",
            AuditLog.resource_id == patient.id,
        )
    )

    assert audit_event is not None
    assert audit_event.actor_user_id == clinician.id
    assert audit_event.action == AuditAction.PATIENT_CREATED.value

def test_viewer_cannot_register_patient(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    viewer = setup["viewer"]

    token = create_access_token(subject=str(viewer.id))

    response = client.post(
        f"/api/v1/organizations/{organization.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "patient_number": "PAT-VIEWER-001",
            "full_name": "Synthetic Viewer Test",
        },
    )

    assert response.status_code == 403

    patient = isolated_db.scalar(
        select(Patient).where(
            Patient.organization_id == organization.id,
            Patient.patient_number == "PAT-VIEWER-001",
        )
    )

    assert patient is None


def test_unauthenticated_user_cannot_register_patient(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]

    response = client.post(
        f"/api/v1/organizations/{organization.id}/patients",
        json={
            "patient_number": "PAT-UNAUTH-001",
            "full_name": "Synthetic Unauthorized Test",
        },
    )

    assert response.status_code == 401

    patient = isolated_db.scalar(
        select(Patient).where(
            Patient.organization_id == organization.id,
            Patient.patient_number == "PAT-UNAUTH-001",
        )
    )

    assert patient is None

def test_duplicate_patient_number_returns_409(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    clinician = setup["clinician"]

    token = create_access_token(subject=str(clinician.id))
    headers = {"Authorization": f"Bearer {token}"}

    url = f"/api/v1/organizations/{organization.id}/patients"

    payload = {
        "patient_number": "PAT-DUP-001",
        "full_name": "Synthetic Duplicate Test",
    }

    # First registration should succeed.
    first_response = client.post(
        url,
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201, first_response.text

    # Same patient number should be rejected.
    second_response = client.post(
        url,
        headers=headers,
        json=payload,
    )

    assert second_response.status_code == 409

    # Only one patient record should exist.
    patients = isolated_db.scalars(
        select(Patient).where(
            Patient.organization_id == organization.id,
            Patient.patient_number == "PAT-DUP-001",
        )
    ).all()

    assert len(patients) == 1

def test_clinician_cannot_register_patient_in_another_hospital(
    isolated_db,
):
    # Create two separate hospitals.
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    clinician_a = hospital_a["clinician"]
    organization_b = hospital_b["organization"]

    token = create_access_token(
        subject=str(clinician_a.id)
    )

    # Hospital A clinician tries to register in Hospital B.
    response = client.post(
        f"/api/v1/organizations/{organization_b.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "patient_number": "PAT-CROSS-001",
            "full_name": "Synthetic Cross Hospital Test",
        },
    )

    # Organization membership dependency must reject access.
    assert response.status_code == 404

    # No patient should have been created in Hospital B.
    patient = isolated_db.scalar(
        select(Patient).where(
            Patient.organization_id == organization_b.id,
            Patient.patient_number == "PAT-CROSS-001",
        )
    )

    assert patient is None

def test_patient_creation_rolls_back_when_audit_fails(
    isolated_db,
    monkeypatch,
):
    from backend.app.api import patients as patient_api

    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]
    clinician = setup["clinician"]

    def simulate_audit_failure(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        patient_api,
        "record_audit_event",
        simulate_audit_failure,
    )

    token = create_access_token(subject=str(clinician.id))

    # TestClient should propagate the simulated exception.
    with pytest.raises(RuntimeError, match="Simulated audit failure"):
        client.post(
            f"/api/v1/organizations/{organization.id}/patients",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient_number": "PAT-ROLLBACK-001",
                "full_name": "Synthetic Rollback Test",
            },
        )

    # Patient must not exist after transaction rollback.
    patient = isolated_db.scalar(
        select(Patient).where(
            Patient.organization_id == organization.id,
            Patient.patient_number == "PAT-ROLLBACK-001",
        )
    )

    assert patient is None

def test_patient_listing_is_isolated_by_hospital(isolated_db):
    # Create two independent hospitals.
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    organization_a = hospital_a["organization"]
    organization_b = hospital_b["organization"]

    # Create synthetic patients in both hospitals.
    patient_a = Patient(
        organization_id=organization_a.id,
        patient_number="A-001",
        full_name="Synthetic Patient A",
        is_active=True,
    )

    patient_b = Patient(
        organization_id=organization_b.id,
        patient_number="B-001",
        full_name="Synthetic Patient B",
        is_active=True,
    )

    isolated_db.add_all([patient_a, patient_b])
    isolated_db.flush()

    # Hospital A clinician requests their patient list.
    clinician_a = hospital_a["clinician"]
    token = create_access_token(subject=str(clinician_a.id))

    response = client.get(
        f"/api/v1/organizations/{organization_a.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    patients = response.json()
    patient_numbers = [p["patient_number"] for p in patients]

    # Hospital A patient must be visible.
    assert "A-001" in patient_numbers

    # Hospital B patient must never be visible.
    assert "B-001" not in patient_numbers

    # Every returned patient belongs to Hospital A.
    assert all(
        p["organization_id"] == str(organization_a.id)
        for p in patients
    )

def test_patient_listing_excludes_inactive_patients(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    isolated_db.add_all([
        Patient(
            organization_id=organization.id,
            patient_number="ACTIVE-001",
            full_name="Synthetic Active Patient",
            is_active=True,
        ),
        Patient(
            organization_id=organization.id,
            patient_number="INACTIVE-001",
            full_name="Synthetic Inactive Patient",
            is_active=False,
        ),
    ])
    isolated_db.flush()

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    numbers = {
        patient["patient_number"]
        for patient in response.json()
    }

    assert "ACTIVE-001" in numbers
    assert "INACTIVE-001" not in numbers


def test_viewer_can_read_patient_listing(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    isolated_db.add(
        Patient(
            organization_id=organization.id,
            patient_number="VIEW-001",
            full_name="Synthetic Viewer Patient",
            is_active=True,
        )
    )
    isolated_db.flush()

    token = create_access_token(
        subject=str(setup["viewer"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert any(
        patient["patient_number"] == "VIEW-001"
        for patient in response.json()
    )


def test_patient_listing_denies_cross_hospital_access(isolated_db):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    token = create_access_token(
        subject=str(hospital_a["clinician"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{hospital_b['organization'].id}/patients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

def test_patient_listing_pagination(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]
    clinician = setup["clinician"]

    # Create five synthetic patients.
    for number in range(1, 6):
        isolated_db.add(
            Patient(
                organization_id=organization.id,
                patient_number=f"PAGE-{number:03d}",
                full_name=f"Synthetic Patient {number}",
                is_active=True,
            )
        )

    isolated_db.flush()

    token = create_access_token(
        subject=str(clinician.id)
    )

    url = f"/api/v1/organizations/{organization.id}/patients"
    headers = {"Authorization": f"Bearer {token}"}

    # Request first two patients.
    first_page = client.get(
        url,
        headers=headers,
        params={"skip": 0, "limit": 2},
    )

    assert first_page.status_code == 200, first_page.text
    assert len(first_page.json()) == 2

    # Request next two patients.
    second_page = client.get(
        url,
        headers=headers,
        params={"skip": 2, "limit": 2},
    )

    assert second_page.status_code == 200, second_page.text
    assert len(second_page.json()) == 2

    # Pages must not contain overlapping patients.
    first_ids = {p["id"] for p in first_page.json()}
    second_ids = {p["id"] for p in second_page.json()}

    assert first_ids.isdisjoint(second_ids)

    # Final page contains one remaining patient.
    last_page = client.get(
        url,
        headers=headers,
        params={"skip": 4, "limit": 2},
    )

    assert last_page.status_code == 200, last_page.text
    assert len(last_page.json()) == 1

@pytest.mark.parametrize(
    "skip,limit",
    [
        (-1, 10),
        (0, 0),
        (0, 101),
    ],
)
def test_patient_listing_rejects_invalid_pagination(
    isolated_db,
    skip,
    limit,
):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    clinician = setup["clinician"]

    token = create_access_token(
        subject=str(clinician.id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "skip": skip,
            "limit": limit,
        },
    )

    assert response.status_code == 422, response.text

def test_clinician_can_get_patient_details(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DETAIL-001",
        full_name="Synthetic Detail Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients/{patient.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == str(patient.id)
    assert response.json()["patient_number"] == "DETAIL-001"
    assert response.json()["organization_id"] == str(organization.id)


def test_patient_details_denies_cross_hospital_access(isolated_db):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    patient_b = Patient(
        organization_id=hospital_b["organization"].id,
        patient_number="DETAIL-CROSS-001",
        full_name="Synthetic Hospital B Patient",
        is_active=True,
    )

    isolated_db.add(patient_b)
    isolated_db.flush()

    token = create_access_token(
        subject=str(hospital_a["clinician"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{hospital_a['organization'].id}/patients/{patient_b.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_patient_details_excludes_inactive_patient(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DETAIL-INACTIVE-001",
        full_name="Synthetic Inactive Patient",
        is_active=False,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients/{patient.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

import uuid


def test_viewer_can_get_patient_details(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DETAIL-VIEWER-001",
        full_name="Synthetic Viewer Detail Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    token = create_access_token(
        subject=str(setup["viewer"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients/{patient.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == str(patient.id)


def test_unauthenticated_user_cannot_get_patient_details(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DETAIL-UNAUTH-001",
        full_name="Synthetic Unauthorized Detail Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients/{patient.id}",
    )

    assert response.status_code == 401


def test_nonexistent_patient_details_returns_404(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    nonexistent_patient_id = uuid.uuid4()

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    response = client.get(
        f"/api/v1/organizations/{organization.id}/patients/{nonexistent_patient_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

def test_clinician_can_update_patient_with_audit_event(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]
    clinician = setup["clinician"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="UPDATE-001",
        full_name="Synthetic Original Patient",
        sex_at_birth="female",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    token = create_access_token(
        subject=str(clinician.id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "full_name": "Synthetic Updated Patient"
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == str(patient_id)
    assert data["full_name"] == "Synthetic Updated Patient"
    assert data["patient_number"] == "UPDATE-001"
    assert data["sex_at_birth"] == "female"

    # Verify the change was saved to the database.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.full_name == "Synthetic Updated Patient"

    # Verify audit logging.
    audit_event = isolated_db.scalar(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.actor_user_id == clinician.id,
            AuditLog.action == AuditAction.PATIENT_UPDATED.value,
            AuditLog.resource_id == patient_id,
        )
    )

    assert audit_event is not None
    assert audit_event.resource_type == "patient"

def test_viewer_cannot_update_patient(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="UPDATE-VIEWER-001",
        full_name="Synthetic Original Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    token = create_access_token(
        subject=str(setup["viewer"].id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Unauthorized Change"},
    )

    assert response.status_code == 403, response.text

    isolated_db.expire_all()
    saved_patient = isolated_db.get(Patient, patient.id)

    assert saved_patient.full_name == "Synthetic Original Patient"


def test_clinician_cannot_update_another_hospitals_patient(isolated_db):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    patient_b = Patient(
        organization_id=hospital_b["organization"].id,
        patient_number="UPDATE-CROSS-001",
        full_name="Synthetic Hospital B Patient",
        is_active=True,
    )

    isolated_db.add(patient_b)
    isolated_db.flush()

    token = create_access_token(
        subject=str(hospital_a["clinician"].id)
    )

    response = client.patch(
        f"/api/v1/organizations/{hospital_a['organization'].id}/patients/{patient_b.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Unauthorized Cross-Hospital Change"},
    )

    assert response.status_code == 404, response.text

    isolated_db.expire_all()
    saved_patient = isolated_db.get(Patient, patient_b.id)

    assert saved_patient.full_name == "Synthetic Hospital B Patient"

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"full_name": None},
        {"full_name": ""},
        {"full_name": "   "},
        {"date_of_birth": "2099-01-01"},
        {"sex_at_birth": "invalid_value"},
    ],
)
def test_patient_update_rejects_invalid_payloads(
    isolated_db,
    payload,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="UPDATE-INVALID-001",
        full_name="Synthetic Original Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 422, response.text

    # Verify invalid updates did not modify patient data.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.full_name == "Synthetic Original Patient"
    assert saved_patient.date_of_birth is None
    assert saved_patient.sex_at_birth is None

    # Invalid requests must not generate update audit events.
    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_UPDATED.value,
        )
    ).all()

    assert len(audit_events) == 0

def test_patient_update_rolls_back_when_audit_fails(
    isolated_db,
    monkeypatch,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="UPDATE-ROLLBACK-001",
        full_name="Synthetic Original Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id
    isolated_db.commit()

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    # Simulate an audit logging failure.
    def failing_audit_event(*args, **kwargs):
        raise RuntimeError("Simulated audit logging failure")

    monkeypatch.setattr(
        "backend.app.api.patients.record_audit_event",
        failing_audit_event,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated audit logging failure",
    ):
        client.patch(
            f"/api/v1/organizations/{organization.id}/patients/{patient_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json={
                "full_name": "Synthetic Unauthorized Persistence"
            },
        )

    # Refresh SQLAlchemy state after rollback.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.full_name == "Synthetic Original Patient"

    # No update audit event should exist.
    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_UPDATED.value,
        )
    ).all()

    assert len(audit_events) == 0

def test_unauthenticated_user_cannot_update_patient(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="UPDATE-UNAUTH-001",
        full_name="Synthetic Original Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    # No Authorization header.
    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}",
        json={
            "full_name": "Unauthorized Update"
        },
    )

    assert response.status_code == 401, response.text

    # Patient information must remain unchanged.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.full_name == "Synthetic Original Patient"

    # No update audit event should be created.
    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_UPDATED.value,
        )
    ).all()

    assert len(audit_events) == 0

def test_clinician_can_clear_nullable_patient_fields(isolated_db):
    from datetime import date

    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]
    clinician = setup["clinician"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="UPDATE-CLEAR-001",
        full_name="Synthetic Original Patient",
        date_of_birth=date(2000, 5, 15),
        sex_at_birth="female",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    token = create_access_token(
        subject=str(clinician.id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "date_of_birth": None,
            "sex_at_birth": None,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["date_of_birth"] is None
    assert data["sex_at_birth"] is None
    assert data["full_name"] == "Synthetic Original Patient"
    assert data["patient_number"] == "UPDATE-CLEAR-001"

    # Verify changes in PostgreSQL.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.date_of_birth is None
    assert saved_patient.sex_at_birth is None
    assert saved_patient.full_name == "Synthetic Original Patient"

    # Verify audit event was recorded.
    audit_event = isolated_db.scalar(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.actor_user_id == clinician.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_UPDATED.value,
        )
    )

    assert audit_event is not None

def test_clinician_can_deactivate_patient_with_audit_event(
    isolated_db,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]
    clinician = setup["clinician"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DEACTIVATE-001",
        full_name="Synthetic Deactivation Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    token = create_access_token(
        subject=str(clinician.id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == str(patient_id)
    assert data["is_active"] is False
    assert data["patient_number"] == "DEACTIVATE-001"

    # Verify the patient still exists in PostgreSQL.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.is_active is False

    # Verify the audit event.
    audit_event = isolated_db.scalar(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.actor_user_id == clinician.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_DEACTIVATED.value,
        )
    )

    assert audit_event is not None
    assert audit_event.resource_type == "patient"

    # Deactivated patients must not appear in active listings.
    list_response = client.get(
        f"/api/v1/organizations/{organization.id}/patients",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert list_response.status_code == 200, list_response.text

    listed_ids = {
        item["id"]
        for item in list_response.json()
    }

    assert str(patient_id) not in listed_ids

def test_viewer_cannot_deactivate_patient(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DEACTIVATE-VIEWER-001",
        full_name="Synthetic Viewer Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    token = create_access_token(
        subject=str(setup["viewer"].id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403, response.text

    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)
    assert saved_patient is not None
    assert saved_patient.is_active is True


def test_clinician_cannot_deactivate_another_hospitals_patient(
    isolated_db,
):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    patient_b = Patient(
        organization_id=hospital_b["organization"].id,
        patient_number="DEACTIVATE-CROSS-001",
        full_name="Synthetic Hospital B Patient",
        is_active=True,
    )

    isolated_db.add(patient_b)
    isolated_db.flush()

    patient_id = patient_b.id

    token = create_access_token(
        subject=str(hospital_a["clinician"].id)
    )

    response = client.patch(
        f"/api/v1/organizations/{hospital_a['organization'].id}/patients/{patient_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text

    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)
    assert saved_patient is not None
    assert saved_patient.is_active is True


def test_already_inactive_patient_cannot_be_deactivated(
    isolated_db,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DEACTIVATE-INACTIVE-001",
        full_name="Synthetic Inactive Patient",
        is_active=False,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    token = create_access_token(
        subject=str(setup["clinician"].id)
    )

    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text

    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)
    assert saved_patient is not None
    assert saved_patient.is_active is False

    # No deactivation audit event should be created.
    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_DEACTIVATED.value,
        )
    ).all()

    assert len(audit_events) == 0

def test_patient_deactivation_rolls_back_when_audit_fails(
    isolated_db,
    monkeypatch,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DEACTIVATE-ROLLBACK-001",
        full_name="Synthetic Rollback Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id
    organization_id = organization.id
    clinician_id = setup["clinician"].id

    # Commit fixture setup into a test savepoint.
    # The outer test transaction still rolls back at teardown.
    isolated_db.commit()

    token = create_access_token(
        subject=str(clinician_id)
    )

    def failing_audit_event(*args, **kwargs):
        raise RuntimeError("Simulated deactivation audit failure")

    monkeypatch.setattr(
        "backend.app.api.patients.record_audit_event",
        failing_audit_event,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated deactivation audit failure",
    ):
        client.patch(
            f"/api/v1/organizations/{organization_id}/patients/{patient_id}/deactivate",
            headers={"Authorization": f"Bearer {token}"},
        )

    # Read fresh database state after rollback.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.is_active is True

    # Failed deactivation must not create an audit event.
    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization_id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_DEACTIVATED.value,
        )
    ).all()

    assert len(audit_events) == 0

def test_unauthenticated_user_cannot_deactivate_patient(
    isolated_db,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    patient = Patient(
        organization_id=organization.id,
        patient_number="DEACTIVATE-UNAUTH-001",
        full_name="Synthetic Unauthenticated Patient",
        is_active=True,
    )

    isolated_db.add(patient)
    isolated_db.flush()

    patient_id = patient.id

    # Request without an Authorization header.
    response = client.patch(
        f"/api/v1/organizations/{organization.id}/patients/{patient_id}/deactivate",
    )

    assert response.status_code == 401, response.text

    # Patient must remain active.
    isolated_db.expire_all()

    saved_patient = isolated_db.get(Patient, patient_id)

    assert saved_patient is not None
    assert saved_patient.is_active is True

    # No deactivation audit event should exist.
    audit_events = isolated_db.scalars(
        select(AuditLog).where(
            AuditLog.organization_id == organization.id,
            AuditLog.resource_id == patient_id,
            AuditLog.action == AuditAction.PATIENT_DEACTIVATED.value,
        )
    ).all()

    assert len(audit_events) == 0
