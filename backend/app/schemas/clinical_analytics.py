
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class AdmissionTrend(BaseModel):
    date: date
    count: int = Field(ge=0)


class ClinicalAnalyticsResponse(BaseModel):
    organization_id: UUID

    # Total hospital encounters
    total_encounters: int = Field(ge=0)

    # Encounters awaiting data quality review
    pending_review: int = Field(ge=0)

    # Counts grouped by data quality status
    data_quality_breakdown: dict[str, int]

    # Counts grouped by encounter type
    encounter_types: dict[str, int]

    # Daily admission counts
    admission_trends: list[AdmissionTrend]

    # Average hospital stay in days
    average_length_of_stay_days: float | None = Field(
        default=None,
        ge=0,
    )
