
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_user,
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from backend.app.db.session import get_db
from backend.app.models.import_job import ImportJob
from backend.app.schemas.import_job import (
    ImportJobListResponse,
    ImportJobResponse,
)
from backend.app.services.audit import (
    AuditAction,
    record_audit_event,
)
from backend.app.services.csv_import import (
    CSVImportError,
    MAX_CSV_SIZE_BYTES,
)
from backend.app.services.encounter_import import (
    save_encounter_import,
)


router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/imports",
    tags=["Hospital CSV Imports"],
)


@router.post("/encounters", status_code=201)
async def upload_encounter_csv(
    organization_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_WRITE
        )
    ),
):
    filename = file.filename or ""

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=422,
            detail="Only CSV files are supported",
        )

    try:
        content = await file.read(MAX_CSV_SIZE_BYTES + 1)

        if len(content) > MAX_CSV_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="CSV file exceeds 5 MB limit",
            )

        # Validate and save CSV import.
        job = save_encounter_import(
            db=db,
            organization_id=organization_id,
            created_by_user_id=current_user.id,
            filename=filename,
            file_content=content,
        )

        # Record the import in the existing audit system.
        record_audit_event(
            db=db,
            organization_id=organization_id,
            actor_user_id=current_user.id,
            action=AuditAction.ENCOUNTER_CSV_IMPORTED,
            resource_type="import_job",
            resource_id=job.id,
        )

        response = {
            "import_job_id": str(job.id),
            "status": job.status,
            "total_rows": job.total_rows,
            "valid_rows": job.valid_rows,
            "invalid_rows": job.invalid_rows,
        }

        # Save encounters, import job and audit event together.
        db.commit()

        return response

    except CSVImportError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        await file.close()


@router.get(
    "",
    response_model=ImportJobListResponse,
)
def list_import_jobs(
    organization_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    total = db.scalar(
        select(func.count(ImportJob.id)).where(
            ImportJob.organization_id == organization_id
        )
    )

    jobs = db.scalars(
        select(ImportJob)
        .where(
            ImportJob.organization_id == organization_id
        )
        .order_by(
            ImportJob.created_at.desc(),
            ImportJob.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return ImportJobListResponse(
        items=[
            ImportJobResponse.model_validate(job)
            for job in jobs
        ],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{import_job_id}",
    response_model=ImportJobResponse,
)
def get_import_job(
    organization_id: UUID,
    import_job_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    job = db.scalar(
        select(ImportJob).where(
            ImportJob.id == import_job_id,
            ImportJob.organization_id == organization_id,
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Import job not found",
        )

    return job
