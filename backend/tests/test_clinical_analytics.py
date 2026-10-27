
from datetime import date

from backend.app.models.encounter import Encounter
from backend.app.services.clinical_analytics import (
    get_clinical_analytics,
)
from backend.tests.test_audit_logging import (
    create_hospital_setup,
)
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import get_db
from backend.tests.test_audit_logging import auth_headers

def test_clinical_analytics_calculations(isolated_db):
    setup = create_hospital_setup(isolated_db)
    organization = setup["organization"]

    encounters = [
        Encounter(
            organization_id=organization.id,
            source_record_id="ANALYTICS-001",
            admission_date=date(2026, 10, 1),
            discharge_date=date(2026, 10, 5),
            encounter_type="inpatient",
            normalized_features={},
            data_quality_status="pending_review",
        ),
        Encounter(
            organization_id=organization.id,
            source_record_id="ANALYTICS-002",
            admission_date=date(2026, 10, 1),
            discharge_date=date(2026, 10, 3),
            encounter_type="inpatient",
            normalized_features={},
            data_quality_status="validated",
        ),
        Encounter(
            organization_id=organization.id,
            source_record_id="ANALYTICS-003",
            admission_date=date(2026, 10, 2),
            discharge_date=None,
            encounter_type="outpatient",
            normalized_features={},
            data_quality_status="pending_review",
        ),
    ]

    isolated_db.add_all(encounters)
    isolated_db.flush()

    result = get_clinical_analytics(
        db=isolated_db,
        organization_id=organization.id,
    )

    assert result["total_encounters"] == 3
    assert result["pending_review"] == 2
    assert result["data_quality_breakdown"] == {
    "pending_review": 2,
    "validated": 1,
}

    assert result["encounter_types"] == {
        "inpatient": 2,
        "outpatient": 1,
    }

    assert result["admission_trends"] == [
        {"date": "2026-10-01", "count": 2},
        {"date": "2026-10-02", "count": 1},
    ]

    # Average of 4 days and 2 days.
    assert result["average_length_of_stay_days"] == 3.0

def test_analytics_endpoint_enforces_hospital_access(isolated_db):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    organization_a = hospital_a["organization"]
    owner_a = hospital_a["owner"]
    owner_b = hospital_b["owner"]

    isolated_db.add(
        Encounter(
            organization_id=organization_a.id,
            source_record_id="ANALYTICS-HTTP-001",
            admission_date=date(2026, 10, 1),
            discharge_date=date(2026, 10, 4),
            encounter_type="inpatient",
            normalized_features={},
            data_quality_status="pending_review",
        )
    )
    isolated_db.flush()

    app.dependency_overrides[get_db] = lambda: isolated_db

    url = (
        f"/api/v1/organizations/"
        f"{organization_a.id}/analytics/overview"
    )

    try:
        with TestClient(app) as client:
            # Authorized hospital owner
            authorized = client.get(
                url,
                headers=auth_headers(owner_a),
            )

            # Owner of another hospital
            cross_hospital = client.get(
                url,
                headers=auth_headers(owner_b),
            )

            # No authentication
            unauthenticated = client.get(url)

        assert authorized.status_code == 200, authorized.text

        data = authorized.json()

        assert data["total_encounters"] == 1
        assert data["pending_review"] == 1
        assert data["average_length_of_stay_days"] == 3.0

        assert cross_hospital.status_code in (403, 404)
        assert unauthenticated.status_code == 401

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_analytics_endpoint_filters_by_admission_date(isolated_db):
    hospital = create_hospital_setup(isolated_db)

    organization = hospital["organization"]
    owner = hospital["owner"]

    encounters = [
        Encounter(
            organization_id=organization.id,
            source_record_id="FILTER-OCT-001",
            admission_date=date(2026, 10, 1),
            discharge_date=date(2026, 10, 5),
            encounter_type="inpatient",
            normalized_features={},
            data_quality_status="pending_review",
        ),
        Encounter(
            organization_id=organization.id,
            source_record_id="FILTER-OCT-002",
            admission_date=date(2026, 10, 20),
            discharge_date=date(2026, 10, 22),
            encounter_type="outpatient",
            normalized_features={},
            data_quality_status="validated",
        ),
        Encounter(
            organization_id=organization.id,
            source_record_id="FILTER-NOV-001",
            admission_date=date(2026, 11, 5),
            discharge_date=date(2026, 11, 8),
            encounter_type="inpatient",
            normalized_features={},
            data_quality_status="pending_review",
        ),
    ]

    isolated_db.add_all(encounters)
    isolated_db.flush()

    app.dependency_overrides[get_db] = lambda: isolated_db

    url = (
        f"/api/v1/organizations/"
        f"{organization.id}/analytics/overview"
    )

    try:
        with TestClient(app) as client:
            october_response = client.get(
                url,
                params={
                    "start_date": "2026-10-01",
                    "end_date": "2026-10-31",
                },
                headers=auth_headers(owner),
            )

            invalid_response = client.get(
                url,
                params={
                    "start_date": "2026-11-01",
                    "end_date": "2026-10-01",
                },
                headers=auth_headers(owner),
            )

        assert october_response.status_code == 200, (
            october_response.text
        )

        data = october_response.json()

        assert data["total_encounters"] == 2
        assert data["pending_review"] == 1

        assert data["encounter_types"] == {
            "inpatient": 1,
            "outpatient": 1,
        }

        assert data["admission_trends"] == [
            {"date": "2026-10-01", "count": 1},
            {"date": "2026-10-20", "count": 1},
        ]

        # October stays: 4 days and 2 days.
        assert data["average_length_of_stay_days"] == 3.0

        # Reversed date ranges must be rejected.
        assert invalid_response.status_code == 422

    finally:
        app.dependency_overrides.pop(get_db, None)

