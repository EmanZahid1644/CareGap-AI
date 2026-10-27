
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from backend.app.db.session import get_db
from backend.app.models.encounter import Encounter
from backend.app.services.care_gap_detection import (
    detect_encounter_gaps,
)


router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/care-gaps",
    tags=["Care Gap Detection"],
)


class CareGapFlag(BaseModel):
    code: str
    category: str
    severity: str
    description: str
    recommendation: str


class EncounterGapResult(BaseModel):
    encounter_id: UUID
    source_record_id: str | None
    gap_count: int = Field(ge=0)
    gaps: list[CareGapFlag]


class CareGapListResponse(BaseModel):
    organization_id: UUID
    scanned_encounters: int = Field(ge=0)
    flagged_encounters: int = Field(ge=0)
    total_gaps: int = Field(ge=0)
    items: list[EncounterGapResult]


@router.get(
    "/encounters",
    response_model=CareGapListResponse,
)
def get_encounter_care_gaps(
    organization_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    """
    Analyze one page of hospital encounters.

    Only returns records belonging to the
    authenticated user's authorized hospital.

    Summary counts apply to the current page.
    """

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be after end_date",
        )

    filters = [
        Encounter.organization_id == organization_id
    ]

    if start_date is not None:
        filters.append(
            Encounter.admission_date >= start_date
        )

    if end_date is not None:
        filters.append(
            Encounter.admission_date <= end_date
        )

    encounters = db.scalars(
        select(Encounter)
        .where(*filters)
        .order_by(
            Encounter.created_at.desc(),
            Encounter.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = []
    total_gaps = 0

    for encounter in encounters:
        gaps = detect_encounter_gaps(encounter)

        if not gaps:
            continue

        total_gaps += len(gaps)

        items.append(
            EncounterGapResult(
                encounter_id=encounter.id,
                source_record_id=encounter.source_record_id,
                gap_count=len(gaps),
                gaps=[
                    CareGapFlag(**gap)
                    for gap in gaps
                ],
            )
        )

    return CareGapListResponse(
        organization_id=organization_id,
        scanned_encounters=len(encounters),
        flagged_encounters=len(items),
        total_gaps=total_gaps,
        items=items,
    )
