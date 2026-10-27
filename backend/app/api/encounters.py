
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.encounter import Encounter
from backend.app.schemas.encounter import EncounterResponse
from backend.app.core.dependencies import (
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from datetime import date

router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/encounters",
    tags=["Hospital Encounters"],
)



@router.get("", response_model=list[EncounterResponse])
def list_encounters(
    organization_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    data_quality_status: str | None = None,
    db: Session = Depends(get_db),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=422,
            detail="start_date cannot be after end_date",
        )

    query = select(Encounter).where(
        Encounter.organization_id == organization_id
    )

    if start_date is not None:
        query = query.where(
            Encounter.admission_date >= start_date
        )

    if end_date is not None:
        query = query.where(
            Encounter.admission_date <= end_date
        )

    if data_quality_status:
        query = query.where(
            Encounter.data_quality_status == data_quality_status
        )

    query = query.order_by(
        Encounter.created_at.desc(),
        Encounter.id.desc(),
    )

    query = query.offset(
        (page - 1) * page_size
    ).limit(page_size)

    return db.scalars(query).all()



@router.get("/{encounter_id}", response_model=EncounterResponse)
def get_encounter(
    organization_id: UUID,
    encounter_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    encounter = db.scalar(
        select(Encounter).where(
            Encounter.id == encounter_id,
            Encounter.organization_id == organization_id,
        )
    )

    if encounter is None:
        raise HTTPException(
            status_code=404,
            detail="Encounter not found",
        )

    return encounter
