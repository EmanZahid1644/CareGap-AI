
from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from backend.app.db.session import get_db
from backend.app.schemas.clinical_analytics import (
    ClinicalAnalyticsResponse,
)
from backend.app.services.clinical_analytics import (
    get_clinical_analytics,
)


router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/analytics",
    tags=["Clinical Analytics"],
)


@router.get(
    "/overview",
    response_model=ClinicalAnalyticsResponse,
)
def clinical_analytics_overview(
    organization_id: UUID,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    # Reject invalid date ranges.
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be after end_date",
        )

    return get_clinical_analytics(
        db=db,
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
    )
