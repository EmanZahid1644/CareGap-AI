
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.encounter import Encounter


def get_clinical_analytics(
    db: Session,
    organization_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """
    Calculate hospital-scoped descriptive analytics.

    Optional date filters apply to admission_date.

    If a date filter is provided, encounters without
    an admission date are excluded.

    Returns aggregated statistics, not patient records.
    """

    # -----------------------------------------
    # 1. Hospital and date filters
    # -----------------------------------------

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

    # -----------------------------------------
    # 2. Total encounters
    # -----------------------------------------

    total_encounters = db.scalar(
        select(
            func.count(Encounter.id)
        ).where(*filters)
    ) or 0

    # -----------------------------------------
    # 3. Pending data quality review
    # -----------------------------------------

    pending_review = db.scalar(
        select(
            func.count(Encounter.id)
        ).where(
            *filters,
            Encounter.data_quality_status == "pending_review",
        )
    ) or 0

    # -----------------------------------------
    # 4. Data quality status distribution
    # -----------------------------------------

    quality_results = db.execute(
        select(
            Encounter.data_quality_status,
            func.count(Encounter.id),
        )
        .where(*filters)
        .group_by(Encounter.data_quality_status)
    ).all()

    data_quality_breakdown = {
        status: count
        for status, count in quality_results
    }

    # -----------------------------------------
    # 5. Encounter type distribution
    # -----------------------------------------

    type_results = db.execute(
        select(
            Encounter.encounter_type,
            func.count(Encounter.id),
        )
        .where(*filters)
        .group_by(Encounter.encounter_type)
    ).all()

    encounter_types = {
        encounter_type or "unknown": count
        for encounter_type, count in type_results
    }

    # -----------------------------------------
    # 6. Admission trends
    # -----------------------------------------

    admission_results = db.execute(
        select(
            Encounter.admission_date,
            func.count(Encounter.id),
        )
        .where(
            *filters,
            Encounter.admission_date.is_not(None),
        )
        .group_by(Encounter.admission_date)
        .order_by(Encounter.admission_date)
    ).all()

    admission_trends = [
        {
            "date": admission_date.isoformat(),
            "count": count,
        }
        for admission_date, count in admission_results
    ]

    # -----------------------------------------
    # 7. Average length of stay
    # -----------------------------------------

    average_length_of_stay = db.scalar(
        select(
            func.avg(
                Encounter.discharge_date
                - Encounter.admission_date
            )
        ).where(
            *filters,
            Encounter.admission_date.is_not(None),
            Encounter.discharge_date.is_not(None),
        )
    )

    # -----------------------------------------
    # 8. Dashboard response
    # -----------------------------------------

    return {
        "organization_id": str(organization_id),

        "total_encounters": total_encounters,

        "pending_review": pending_review,

        "data_quality_breakdown": data_quality_breakdown,

        "encounter_types": encounter_types,

        "admission_trends": admission_trends,

        "average_length_of_stay_days": (
            round(float(average_length_of_stay), 2)
            if average_length_of_stay is not None
            else None
        ),
    }
