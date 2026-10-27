
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    import_job_id: UUID | None

    source_record_id: str | None

    admission_date: date | None
    discharge_date: date | None

    encounter_type: str | None

    normalized_features: dict[str, Any] = Field(
        default_factory=dict
    )

    data_quality_status: str

    created_at: datetime
    updated_at: datetime
