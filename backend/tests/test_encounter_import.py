
from pathlib import Path

from sqlalchemy import select
from uuid import UUID
from backend.app.models.encounter import Encounter
from backend.app.models.import_job import ImportJob
from backend.app.services.encounter_import import save_encounter_import
from backend.tests.test_audit_logging import create_hospital_setup
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.dependencies import get_db
from backend.tests.test_audit_logging import auth_headers

from sqlalchemy import select

from backend.app.models.audit import AuditLog
from backend.app.services.audit import AuditAction

def test_csv_import_saves_valid_encounters_and_reports_errors(
    isolated_db,
):
    # Create a synthetic hospital and authorized user.
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    # Read the synthetic sample CSV.
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "sample_encounters.csv"

    file_content = csv_path.read_bytes()

    # Run actual import service.
    job = save_encounter_import(
        db=isolated_db,
        organization_id=organization.id,
        created_by_user_id=owner.id,
        filename="sample_encounters.csv",
        file_content=file_content,
    )

    isolated_db.flush()

    assert job.status == "completed_with_errors"
    assert job.total_rows == 5
    assert job.valid_rows == 2
    assert job.invalid_rows == 3

    # Reload from PostgreSQL.
    isolated_db.expire_all()

    saved_job = isolated_db.get(ImportJob, job.id)

    assert saved_job is not None
    assert saved_job.source_filename == "sample_encounters.csv"
    assert saved_job.completed_at is not None

    # Fetch encounters created by this import.
    encounters = isolated_db.scalars(
        select(Encounter).where(
            Encounter.organization_id == organization.id,
            Encounter.import_job_id == job.id,
        )
    ).all()

    assert len(encounters) == 2

    source_ids = {
        encounter.source_record_id
        for encounter in encounters
    }

    assert source_ids == {"SYN-001", "SYN-002"}

    # Verify normalized clinical features.
    encounter_by_source = {
        encounter.source_record_id: encounter
        for encounter in encounters
    }

    assert (
        encounter_by_source["SYN-001"]
        .normalized_features["age"]
        == 45
    )

    assert (
        encounter_by_source["SYN-002"]
        .normalized_features["diabetes"]
        is False
    )

    # Check that invalid row details were recorded.
    assert saved_job.error_summary is not None
    assert "Duplicate source_record_id" in saved_job.error_summary

def test_authorized_hospital_owner_can_upload_csv(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    # Route all API database operations to the isolated test session.
    app.dependency_overrides[get_db] = lambda: isolated_db

    project_root = Path(__file__).resolve().parents[2]
    csv_content = (
        project_root / "sample_encounters.csv"
    ).read_bytes()

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/organizations/{organization.id}"
                "/imports/encounters",
                headers=auth_headers(owner),
                files={
                    "file": (
                        "sample_encounters.csv",
                        csv_content,
                        "text/csv",
                    )
                },
            )

        assert response.status_code == 201, response.text

        data = response.json()

        assert data["status"] == "completed_with_errors"
        assert data["total_rows"] == 5
        assert data["valid_rows"] == 2
        assert data["invalid_rows"] == 3
        assert "import_job_id" in data

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_unauthorized_users_cannot_upload_csv(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    viewer = setup["viewer"]

    app.dependency_overrides[get_db] = lambda: isolated_db

    csv_content = (
        "source_record_id,admission_date,"
        "discharge_date,encounter_type\n"
        "SYN-SEC-001,2026-10-01,2026-10-03,inpatient\n"
    ).encode("utf-8")

    try:
        with TestClient(app) as client:
            # No authentication token.
            unauthenticated = client.post(
                f"/api/v1/organizations/{organization.id}"
                "/imports/encounters",
                files={
                    "file": (
                        "sample.csv",
                        csv_content,
                        "text/csv",
                    )
                },
            )

            # Read-only hospital staff member.
            read_only = client.post(
                f"/api/v1/organizations/{organization.id}"
                "/imports/encounters",
                headers=auth_headers(viewer),
                files={
                    "file": (
                        "sample.csv",
                        csv_content,
                        "text/csv",
                    )
                },
            )

        assert unauthenticated.status_code == 401
        assert read_only.status_code == 403

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_staff_cannot_upload_to_another_hospital(isolated_db):
    # Create two separate hospitals.
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    clinician_a = hospital_a["clinician"]
    organization_b = hospital_b["organization"]

    app.dependency_overrides[get_db] = lambda: isolated_db

    csv_content = (
        "source_record_id,admission_date,"
        "discharge_date,encounter_type\n"
        "SYN-CROSS-001,2026-10-01,2026-10-03,inpatient\n"
    ).encode("utf-8")

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/organizations/{organization_b.id}"
                "/imports/encounters",
                headers=auth_headers(clinician_a),
                files={
                    "file": (
                        "cross_hospital.csv",
                        csv_content,
                        "text/csv",
                    )
                },
            )

        assert response.status_code in (403, 404)

        # Rejected request must not create import records.
        jobs = isolated_db.scalars(
            select(ImportJob).where(
                ImportJob.organization_id == organization_b.id
            )
        ).all()

        assert len(jobs) == 0

        encounters = isolated_db.scalars(
            select(Encounter).where(
                Encounter.organization_id == organization_b.id
            )
        ).all()

        assert len(encounters) == 0

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_reimport_same_csv_skips_existing_encounters(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    project_root = Path(__file__).resolve().parents[2]
    csv_content = (
        project_root / "sample_encounters.csv"
    ).read_bytes()

    # First import.
    first_job = save_encounter_import(
        db=isolated_db,
        organization_id=organization.id,
        created_by_user_id=owner.id,
        filename="sample_encounters.csv",
        file_content=csv_content,
    )

    assert first_job.total_rows == 5
    assert first_job.valid_rows == 2
    assert first_job.invalid_rows == 3

    # Import the exact same CSV again.
    second_job = save_encounter_import(
        db=isolated_db,
        organization_id=organization.id,
        created_by_user_id=owner.id,
        filename="sample_encounters.csv",
        file_content=csv_content,
    )

    assert second_job.total_rows == 5
    assert second_job.valid_rows == 0
    assert second_job.invalid_rows == 5
    assert second_job.status == "completed_with_errors"

    # Confirm the hospital still has only two encounters.
    encounters = isolated_db.scalars(
        select(Encounter).where(
            Encounter.organization_id == organization.id
        )
    ).all()

    assert len(encounters) == 2

    # Both import jobs should exist for auditability.
    jobs = isolated_db.scalars(
        select(ImportJob).where(
            ImportJob.organization_id == organization.id
        )
    ).all()

    assert len(jobs) == 2

    # Confirm duplicates were reported.
    assert "Encounter already exists" in second_job.error_summary

def test_database_conflict_is_handled_without_duplicate_insert(
    isolated_db,
):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    csv_content = (
        "source_record_id,admission_date,"
        "discharge_date,encounter_type\n"
        "SYN-CONFLICT-001,2026-10-01,"
        "2026-10-03,inpatient\n"
    ).encode("utf-8")

    # Insert an encounter before running the import.
    existing = Encounter(
        organization_id=organization.id,
        source_record_id="SYN-CONFLICT-001",
        admission_date=None,
        discharge_date=None,
        encounter_type="inpatient",
        normalized_features={},
        data_quality_status="valid",
    )

    isolated_db.add(existing)
    isolated_db.flush()

    # Import the same source record.
    job = save_encounter_import(
        db=isolated_db,
        organization_id=organization.id,
        created_by_user_id=owner.id,
        filename="conflict.csv",
        file_content=csv_content,
    )

    assert job.total_rows == 1
    assert job.valid_rows == 0
    assert job.invalid_rows == 1
    assert job.status == "completed_with_errors"

    encounters = isolated_db.scalars(
        select(Encounter).where(
            Encounter.organization_id == organization.id,
            Encounter.source_record_id == "SYN-CONFLICT-001",
        )
    ).all()

    assert len(encounters) == 1

def test_import_history_and_detail_endpoints(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    csv_content = (
        "source_record_id,admission_date,"
        "discharge_date,encounter_type\n"
        "SYN-HISTORY-001,2026-10-01,2026-10-03,inpatient\n"
    ).encode("utf-8")

    # Create one import job.
    job = save_encounter_import(
        db=isolated_db,
        organization_id=organization.id,
        created_by_user_id=owner.id,
        filename="history.csv",
        file_content=csv_content,
    )

    job_id = job.id

    app.dependency_overrides[get_db] = lambda: isolated_db

    base_url = (
        f"/api/v1/organizations/{organization.id}/imports"
    )

    try:
        with TestClient(app) as client:

            # GET import history.
            history_response = client.get(
                base_url,
                headers=auth_headers(owner),
            )

            assert history_response.status_code == 200, (
                history_response.text
            )

            history = history_response.json()

            assert history["total"] == 1
            assert history["page"] == 1
            assert history["page_size"] == 20
            assert len(history["items"]) == 1

            assert (
                history["items"][0]["source_filename"]
                == "history.csv"
            )

            # GET individual import job.
            detail_response = client.get(
                f"{base_url}/{job_id}",
                headers=auth_headers(owner),
            )

            assert detail_response.status_code == 200, (
                detail_response.text
            )

            detail = detail_response.json()

            assert detail["id"] == str(job_id)
            assert detail["status"] == "completed"
            assert detail["total_rows"] == 1
            assert detail["valid_rows"] == 1
            assert detail["invalid_rows"] == 0

            # Row-level error details must not be exposed.
            assert "error_summary" not in detail

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_cross_hospital_import_history_is_blocked(isolated_db):
    hospital_a = create_hospital_setup(isolated_db)
    hospital_b = create_hospital_setup(isolated_db)

    clinician_a = hospital_a["clinician"]
    organization_b = hospital_b["organization"]
    owner_b = hospital_b["owner"]

    csv_content = (
        "source_record_id,admission_date,"
        "discharge_date,encounter_type\n"
        "SYN-PRIVATE-001,2026-10-01,"
        "2026-10-03,inpatient\n"
    ).encode("utf-8")

    # Create an import belonging to Hospital B.
    job_b = save_encounter_import(
        db=isolated_db,
        organization_id=organization_b.id,
        created_by_user_id=owner_b.id,
        filename="hospital_b.csv",
        file_content=csv_content,
    )

    app.dependency_overrides[get_db] = lambda: isolated_db

    base_url = (
        f"/api/v1/organizations/{organization_b.id}/imports"
    )

    try:
        with TestClient(app) as client:

            # Hospital A clinician requests Hospital B history.
            history_response = client.get(
                base_url,
                headers=auth_headers(clinician_a),
            )

            # Hospital A clinician requests Hospital B import details.
            detail_response = client.get(
                f"{base_url}/{job_b.id}",
                headers=auth_headers(clinician_a),
            )

        assert history_response.status_code in (403, 404)
        assert detail_response.status_code in (403, 404)

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_import_history_pagination(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    # Create five synthetic import jobs.
    for index in range(5):
        csv_content = (
            "source_record_id,admission_date,"
            "discharge_date,encounter_type\n"
            f"SYN-PAGE-{index},2026-10-01,"
            "2026-10-03,inpatient\n"
        ).encode("utf-8")

        save_encounter_import(
            db=isolated_db,
            organization_id=organization.id,
            created_by_user_id=owner.id,
            filename=f"batch_{index}.csv",
            file_content=csv_content,
        )

    app.dependency_overrides[get_db] = lambda: isolated_db

    base_url = (
        f"/api/v1/organizations/{organization.id}/imports"
    )

    try:
        with TestClient(app) as client:
            page_1 = client.get(
                f"{base_url}?page=1&page_size=2",
                headers=auth_headers(owner),
            )

            page_2 = client.get(
                f"{base_url}?page=2&page_size=2",
                headers=auth_headers(owner),
            )

            page_3 = client.get(
                f"{base_url}?page=3&page_size=2",
                headers=auth_headers(owner),
            )

        assert page_1.status_code == 200
        assert page_2.status_code == 200
        assert page_3.status_code == 200

        first = page_1.json()
        second = page_2.json()
        third = page_3.json()

        assert first["total"] == 5
        assert len(first["items"]) == 2
        assert len(second["items"]) == 2
        assert len(third["items"]) == 1

        # Every import should appear exactly once.
        all_ids = [
            item["id"]
            for page in (first, second, third)
            for item in page["items"]
        ]

        assert len(set(all_ids)) == 5

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_csv_upload_creates_audit_event(isolated_db):
    setup = create_hospital_setup(isolated_db)

    organization = setup["organization"]
    owner = setup["owner"]

    csv_content = (
        "source_record_id,admission_date,"
        "discharge_date,encounter_type\n"
        "SYN-AUDIT-001,2026-10-01,"
        "2026-10-03,inpatient\n"
    ).encode("utf-8")

    app.dependency_overrides[get_db] = lambda: isolated_db

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/organizations/"
                f"{organization.id}/imports/encounters",
                headers=auth_headers(owner),
                files={
                    "file": (
                        "audit_test.csv",
                        csv_content,
                        "text/csv",
                    )
                },
            )

        assert response.status_code == 201, response.text

        import_job_id = UUID(response.json()["import_job_id"])

        audit_events = isolated_db.scalars(
            select(AuditLog).where(
                AuditLog.organization_id == organization.id,
                AuditLog.actor_user_id == owner.id,
                AuditLog.action == (
                    AuditAction.ENCOUNTER_CSV_IMPORTED.value
                ),
                AuditLog.resource_type == "import_job",
                AuditLog.resource_id == import_job_id,
            )
        ).all()

        assert len(audit_events) == 1

    finally:
        app.dependency_overrides.pop(get_db, None)
