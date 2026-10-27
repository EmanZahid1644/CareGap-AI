
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base
from typing import TYPE_CHECKING

from backend.app.models.identity import Organization
if TYPE_CHECKING:
    from backend.app.models.patient import Patient

class Patient(Base):
    __tablename__ = "patients"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "patient_number",
            name="uq_patient_organization_number",
        ),
        Index(
            "ix_patients_organization_created",
            "organization_id",
            "created_at",
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

    patient_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    sex_at_birth: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="patients",
    )
