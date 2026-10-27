
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.encounter import Encounter
from backend.app.models.import_job import ImportJob
from backend.app.services.csv_import import validate_encounter_csv
from sqlalchemy.dialects.postgresql import insert as pg_insert

def save_encounter_import(
    db: Session,
    organization_id: UUID,
    created_by_user_id: UUID,
    filename: str,
    file_content: bytes,
) -> ImportJob:

    # STEP 1: Validate the uploaded CSV.
    result = validate_encounter_csv(file_content)

    # STEP 2: Collect source IDs from valid CSV rows.
    incoming_ids = [
        row.source_record_id
        for row in result.valid_rows
    ]

    # STEP 3: Find existing encounters in this hospital only.
    existing_ids = set(
        db.scalars(
            select(Encounter.source_record_id).where(
                Encounter.organization_id == organization_id,
                Encounter.source_record_id.in_(incoming_ids),
            )
        ).all()
    )

    # STEP 4: Separate new records from duplicates.
    new_rows = []
    duplicate_errors = []

    for row in result.valid_rows:
        if row.source_record_id in existing_ids:
            duplicate_errors.append({
                "errors": [
                    "Encounter already exists in this hospital"
                ],
            })
        else:
            new_rows.append(row)

    # Include duplicate records in the invalid-row count.
    result.invalid_rows.extend(duplicate_errors)
    result.valid_rows = new_rows

    # STEP 5: Create the import job.
    job = ImportJob(
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        source_filename=filename,
        status="processing",
        total_rows=result.total_rows,
        valid_rows=len(result.valid_rows),
        invalid_rows=len(result.invalid_rows),
        error_summary=json.dumps(result.invalid_rows),
        started_at=datetime.now(timezone.utc),
    )

    db.add(job)
    db.flush()

    # STEP 6: Save only new, valid encounters.
    
    # STEP 6: Insert valid encounters safely.
    # PostgreSQL prevents duplicate source IDs per hospital.

    inserted_count = 0
    conflict_errors = []

    for row in result.valid_rows:

        features = row.model_dump(
            exclude={
                "source_record_id",
                "admission_date",
                "discharge_date",
                "encounter_type",
            },
            exclude_none=True,
            mode="json",
        )

        statement = (
            pg_insert(Encounter)
            .values(
                organization_id=organization_id,
                import_job_id=job.id,
                source_record_id=row.source_record_id,
                admission_date=row.admission_date,
                discharge_date=row.discharge_date,
                encounter_type=row.encounter_type,
                normalized_features=features,
                data_quality_status="valid",
            )
            .on_conflict_do_nothing(
                index_elements=[
                    "organization_id",
                    "source_record_id",
                ],
                index_where=(
                    Encounter.source_record_id.is_not(None)
                ),
            )
            .returning(Encounter.id)
        )

        inserted_id = db.execute(statement).scalar_one_or_none()

        if inserted_id is not None:
            inserted_count += 1
        else:
            conflict_errors.append({
                "errors": [
                    "Encounter already exists in this hospital"
                ],
            })

    # STEP 7: Update import statistics using actual inserts.

    result.invalid_rows.extend(conflict_errors)

    job.valid_rows = inserted_count
    job.invalid_rows = len(result.invalid_rows)
    job.error_summary = json.dumps(result.invalid_rows)

    job.status = (
        "completed"
        if job.invalid_rows == 0
        else "completed_with_errors"
    )

    job.completed_at = datetime.now(timezone.utc)

    # The API caller controls commit and rollback.
    db.flush()

    return job
