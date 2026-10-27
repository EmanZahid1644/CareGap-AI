import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import date
from backend.app.schemas.encounter import EncounterResponse
from sqlalchemy import select

from backend.app.models.encounter import Encounter
from backend.tests.test_audit_logging import (
    create_hospital_setup,
)
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.tests.test_audit_logging import auth_headers

def test_create_encounter_with_normalized_features(isolated_db):
    # Create a synthetic hospital and its staff.
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    # Synthetic encounter data only.
    encounter = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-ENC-001",
        admission_date=date(2026, 10, 1),
        discharge_date=date(2026, 10, 5),
        encounter_type="inpatient",
        normalized_features={
            "age": 45,
            "length_of_stay": 4,
            "prior_admissions": 2,
            "diabetes": True,
        },
    )

    isolated_db.add(encounter)
    isolated_db.flush()

    encounter_id = encounter.id

    # Reload the record from PostgreSQL.
    isolated_db.expire_all()

    saved_encounter = isolated_db.scalar(
        select(Encounter).where(
            Encounter.id == encounter_id,
            Encounter.organization_id == organization.id,
        )
    )

    assert saved_encounter is not None

    # Verify hospital ownership.
    assert saved_encounter.organization_id == organization.id

    # Verify encounter information.
    assert saved_encounter.source_record_id == "SYN-ENC-001"
    assert saved_encounter.admission_date == date(2026, 10, 1)
    assert saved_encounter.discharge_date == date(2026, 10, 5)
    assert saved_encounter.encounter_type == "inpatient"

    # Verify PostgreSQL JSONB storage.
    assert saved_encounter.normalized_features == {
        "age": 45,
        "length_of_stay": 4,
        "prior_admissions": 2,
        "diabetes": True,
    }

    # Verify default values.
    assert saved_encounter.data_quality_status == "pending_review"
    assert saved_encounter.import_job_id is None

    # Verify database timestamps.
    assert saved_encounter.created_at is not None
    assert saved_encounter.updated_at is not None

def test_encounter_requires_existing_organization(isolated_db):
    # Generate a random organization ID that does not exist.
    nonexistent_organization_id = uuid.uuid4()

    encounter = Encounter(
        organization_id=nonexistent_organization_id,
        source_record_id="SYN-INVALID-ORG-001",
        normalized_features={
            "age": 50,
            "prior_admissions": 1,
        },
    )

    isolated_db.add(encounter)

    # PostgreSQL must reject an invalid organization reference.
    with pytest.raises(IntegrityError) as exc_info:
        isolated_db.flush()

    # PostgreSQL foreign key violation.
    assert getattr(exc_info.value.orig, "sqlstate", None) == "23503"

    # Restore the SQLAlchemy session after the failed flush.
    isolated_db.rollback()

def test_encounter_rejects_discharge_before_admission(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    encounter = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-INVALID-DATES-001",
        admission_date=date(2026, 10, 10),
        discharge_date=date(2026, 10, 5),
        encounter_type="inpatient",
        normalized_features={
            "age": 45,
            "prior_admissions": 1,
        },
    )

    isolated_db.add(encounter)

    # PostgreSQL must reject discharge before admission.
    with pytest.raises(IntegrityError) as exc_info:
        isolated_db.flush()

    # PostgreSQL CHECK constraint violation.
    assert getattr(exc_info.value.orig, "sqlstate", None) == "23514"

    constraint_name = getattr(
        getattr(exc_info.value.orig, "diag", None),
        "constraint_name",
        None,
    )

    assert (
        constraint_name
        == "ck_encounters_discharge_not_before_admission"
    )

    # Restore the session after failed insert.
    isolated_db.rollback()

@pytest.mark.parametrize(
    "admission_date, discharge_date",
    [
        (date(2026, 10, 10), date(2026, 10, 10)),
        (date(2026, 10, 10), date(2026, 10, 15)),
        (None, date(2026, 10, 15)),
        (date(2026, 10, 10), None),
        (None, None),
    ],
)
def test_encounter_accepts_valid_or_missing_dates(
    isolated_db,
    admission_date,
    discharge_date,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    encounter = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-VALID-DATES-001",
        admission_date=admission_date,
        discharge_date=discharge_date,
        encounter_type="inpatient",
        normalized_features={},
    )

    isolated_db.add(encounter)
    isolated_db.flush()

    encounter_id = encounter.id

    # Reload from PostgreSQL.
    isolated_db.expire_all()

    saved_encounter = isolated_db.get(
        Encounter,
        encounter_id,
    )

    assert saved_encounter is not None
    assert saved_encounter.admission_date == admission_date
    assert saved_encounter.discharge_date == discharge_date

def test_encounter_queries_are_scoped_to_organization(isolated_db):
    # Create two separate synthetic hospitals.
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    organization_a = hospital_a["organization"]
    organization_b = hospital_b["organization"]

    encounter_a = Encounter(
        organization_id=organization_a.id,
        source_record_id="SYN-HOSPITAL-A-001",
        admission_date=date(2026, 10, 1),
        discharge_date=date(2026, 10, 3),
        encounter_type="inpatient",
        normalized_features={"prior_admissions": 1},
    )

    encounter_b = Encounter(
        organization_id=organization_b.id,
        source_record_id="SYN-HOSPITAL-B-001",
        admission_date=date(2026, 10, 5),
        discharge_date=date(2026, 10, 8),
        encounter_type="inpatient",
        normalized_features={"prior_admissions": 2},
    )

    isolated_db.add_all([encounter_a, encounter_b])
    isolated_db.flush()

    encounter_a_id = encounter_a.id
    encounter_b_id = encounter_b.id

    isolated_db.expire_all()

    # Hospital A query must return only Hospital A records.
    hospital_a_encounters = isolated_db.scalars(
        select(Encounter).where(
            Encounter.organization_id == organization_a.id
        )
    ).all()

    hospital_a_ids = {
        encounter.id for encounter in hospital_a_encounters
    }

    assert encounter_a_id in hospital_a_ids
    assert encounter_b_id not in hospital_a_ids

    # Hospital B query must return only Hospital B records.
    hospital_b_encounters = isolated_db.scalars(
        select(Encounter).where(
            Encounter.organization_id == organization_b.id
        )
    ).all()

    hospital_b_ids = {
        encounter.id for encounter in hospital_b_encounters
    }

    assert encounter_b_id in hospital_b_ids
    assert encounter_a_id not in hospital_b_ids

def test_encounter_jsonb_features_are_independent(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    encounter_a = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-JSON-A-001",
        normalized_features={
            "age": 45,
            "prior_admissions": 1,
        },
    )

    encounter_b = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-JSON-B-001",
        normalized_features={
            "age": 60,
            "prior_admissions": 3,
        },
    )

    isolated_db.add_all([encounter_a, encounter_b])
    isolated_db.flush()

    encounter_a_id = encounter_a.id
    encounter_b_id = encounter_b.id

    # Replace Encounter A's features.
    encounter_a.normalized_features = {
        "age": 46,
        "prior_admissions": 2,
    }

    isolated_db.flush()
    isolated_db.expire_all()

    saved_a = isolated_db.get(Encounter, encounter_a_id)
    saved_b = isolated_db.get(Encounter, encounter_b_id)

    assert saved_a is not None
    assert saved_b is not None

    assert saved_a.normalized_features == {
        "age": 46,
        "prior_admissions": 2,
    }

    # Encounter B must remain unchanged.
    assert saved_b.normalized_features == {
        "age": 60,
        "prior_admissions": 3,
    }

def test_encounter_response_schema_serializes_database_record(
    isolated_db,
):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    encounter = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-SCHEMA-001",
        admission_date=date(2026, 10, 1),
        discharge_date=date(2026, 10, 5),
        encounter_type="inpatient",
        normalized_features={
            "age": 45,
            "prior_admissions": 2,
            "diabetes": True,
        },
    )

    isolated_db.add(encounter)
    isolated_db.flush()
    isolated_db.refresh(encounter)

    response = EncounterResponse.model_validate(encounter)

    assert response.id == encounter.id
    assert response.organization_id == organization.id
    assert response.source_record_id == "SYN-SCHEMA-001"
    assert response.admission_date == date(2026, 10, 1)
    assert response.discharge_date == date(2026, 10, 5)
    assert response.encounter_type == "inpatient"
    assert response.normalized_features["age"] == 45
    assert response.normalized_features["diabetes"] is True
    assert response.data_quality_status == "pending_review"
    assert response.created_at is not None
    assert response.updated_at is not None

    # Confirm that the response is JSON serializable.
    serialized = response.model_dump(mode="json")

    assert isinstance(serialized["id"], str)
    assert isinstance(serialized["created_at"], str)
    assert serialized["normalized_features"]["prior_admissions"] == 2

def test_encounter_list_api_returns_only_own_hospital_records(
    isolated_db,
):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    organization_a = hospital_a["organization"]
    organization_b = hospital_b["organization"]

    isolated_db.add_all(
        [
            Encounter(
                organization_id=organization_a.id,
                source_record_id="SYN-API-A-001",
                normalized_features={"age": 45},
            ),
            Encounter(
                organization_id=organization_b.id,
                source_record_id="SYN-API-B-001",
                normalized_features={"age": 60},
            ),
        ]
    )
    isolated_db.commit()

    client = TestClient(app)

    url = (
        f"/api/v1/organizations/"
        f"{organization_a.id}/encounters"
    )

    response = client.get(
        url,
        headers=auth_headers(hospital_a["clinician"]),
    )

    assert response.status_code == 200, response.text

    records = response.json()

    assert len(records) == 1
    assert records[0]["source_record_id"] == "SYN-API-A-001"
    assert records[0]["organization_id"] == str(organization_a.id)


def test_encounter_api_rejects_cross_hospital_access(
    isolated_db,
):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    encounter = Encounter(
        organization_id=hospital_a["organization"].id,
        source_record_id="SYN-PRIVATE-001",
        normalized_features={},
    )

    isolated_db.add(encounter)
    isolated_db.commit()

    client = TestClient(app)

    # Hospital B clinician attempts to access Hospital A.
    url = (
        f"/api/v1/organizations/"
        f"{hospital_a['organization'].id}/encounters/"
        f"{encounter.id}"
    )

    response = client.get(
        url,
        headers=auth_headers(hospital_b["clinician"]),
    )

    assert response.status_code == 404


def test_encounter_api_requires_authentication(isolated_db):
    hospital = create_hospital_setup(isolated_db)
    isolated_db.commit()

    client = TestClient(app)

    url = (
        f"/api/v1/organizations/"
        f"{hospital['organization'].id}/encounters"
    )

    response = client.get(url)

    assert response.status_code == 401

@pytest.mark.parametrize(
    "query_params, expected_source_ids",
    [
        (
            {
                "start_date": "2026-10-10",
                "end_date": "2026-10-20",
            },
            {"SYN-FILTER-002", "SYN-FILTER-003"},
        ),
        (
            {"data_quality_status": "pending_review"},
            {"SYN-FILTER-001", "SYN-FILTER-003"},
        ),
        (
            {
                "start_date": "2026-10-10",
                "end_date": "2026-10-20",
                "data_quality_status": "pending_review",
            },
            {"SYN-FILTER-003"},
        ),
    ],
)
def test_encounter_api_filters(
    isolated_db,
    query_params,
    expected_source_ids,
):
    hospital = create_hospital_setup(isolated_db)
    organization = hospital["organization"]

    records = [
        Encounter(
            organization_id=organization.id,
            source_record_id="SYN-FILTER-001",
            admission_date=date(2026, 10, 1),
            data_quality_status="pending_review",
            normalized_features={},
        ),
        Encounter(
            organization_id=organization.id,
            source_record_id="SYN-FILTER-002",
            admission_date=date(2026, 10, 12),
            data_quality_status="valid",
            normalized_features={},
        ),
        Encounter(
            organization_id=organization.id,
            source_record_id="SYN-FILTER-003",
            admission_date=date(2026, 10, 18),
            data_quality_status="pending_review",
            normalized_features={},
        ),
    ]

    isolated_db.add_all(records)
    isolated_db.commit()

    client = TestClient(app)

    url = (
        f"/api/v1/organizations/"
        f"{organization.id}/encounters"
    )

    response = client.get(
        url,
        params=query_params,
        headers=auth_headers(hospital["clinician"]),
    )

    assert response.status_code == 200, response.text

    actual_source_ids = {
        record["source_record_id"]
        for record in response.json()
    }

    assert actual_source_ids == expected_source_ids


def test_encounter_api_pagination(isolated_db):
    hospital = create_hospital_setup(isolated_db)
    organization = hospital["organization"]

    for index in range(5):
        isolated_db.add(
            Encounter(
                organization_id=organization.id,
                source_record_id=f"SYN-PAGE-{index}",
                normalized_features={},
            )
        )

    isolated_db.commit()

    client = TestClient(app)

    url = (
        f"/api/v1/organizations/"
        f"{organization.id}/encounters"
    )

    headers = auth_headers(hospital["clinician"])

    page_1 = client.get(
        url,
        params={"page": 1, "page_size": 2},
        headers=headers,
    )

    page_2 = client.get(
        url,
        params={"page": 2, "page_size": 2},
        headers=headers,
    )

    assert page_1.status_code == 200
    assert page_2.status_code == 200

    assert len(page_1.json()) == 2
    assert len(page_2.json()) == 2

    page_1_ids = {record["id"] for record in page_1.json()}
    page_2_ids = {record["id"] for record in page_2.json()}

    assert page_1_ids.isdisjoint(page_2_ids)


def test_encounter_api_rejects_invalid_date_range(isolated_db):
    hospital = create_hospital_setup(isolated_db)
    isolated_db.commit()

    client = TestClient(app)

    url = (
        f"/api/v1/organizations/"
        f"{hospital['organization'].id}/encounters"
    )

    response = client.get(
        url,
        params={
            "start_date": "2026-10-20",
            "end_date": "2026-10-10",
        },
        headers=auth_headers(hospital["clinician"]),
    )

    assert response.status_code == 422
