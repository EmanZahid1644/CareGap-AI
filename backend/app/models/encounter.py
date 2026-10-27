
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.import_job import ImportJob  # noqa: F401
from backend.app.db.session import Base
from sqlalchemy import Index, text


class Encounter(Base):
    __tablename__ = "encounters"

    __table_args__ = (
         CheckConstraint(
        "discharge_date IS NULL OR admission_date IS NULL "
        "OR discharge_date >= admission_date",
        name="ck_encounters_discharge_not_before_admission",
    ),
    Index(
        "ix_encounters_organization_admission",
        "organization_id",
        "admission_date",
    ),
    Index(
        "ix_encounters_organization_created",
        "organization_id",
        "created_at",
    ),
    Index(
    "uq_encounters_org_source_record_id",
    "organization_id",
    "source_record_id",
    unique=True,
    postgresql_where=text("source_record_id IS NOT NULL"),
),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Nullable until the import_jobs table is implemented.
    import_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="RESTRICT"),
        nullable=True,
    )

    source_record_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    admission_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    discharge_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    encounter_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    normalized_features: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    data_quality_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_review",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
