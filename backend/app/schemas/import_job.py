
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    created_by_user_id: UUID
    source_filename: str
    status: str

    total_rows: int
    valid_rows: int
    invalid_rows: int

    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ImportJobListResponse(BaseModel):
    items: list[ImportJobResponse]
    total: int
    page: int
    page_size: int
