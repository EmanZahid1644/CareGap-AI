
import uuid
from enum import Enum

from sqlalchemy.orm import Session

from backend.app.models.audit import AuditLog


class AuditAction(str, Enum):
    MEMBERSHIP_CREATED = "membership.created"
    MEMBERSHIP_ROLE_UPDATED = "membership.role_updated"
    MEMBERSHIP_DEACTIVATED = "membership.deactivated"
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"
    PATIENT_DEACTIVATED = "patient.deactivated"
    ENCOUNTER_CSV_IMPORTED = "encounter.csv_imported"

def record_audit_event(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: AuditAction,
    resource_type: str,
    resource_id: uuid.UUID,
) -> AuditLog:
    """
    Stage an audit event in the current database transaction.

    The caller is responsible for committing the transaction.
    This function intentionally does not commit.
    """

    event = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action.value,
        resource_type=resource_type,
        resource_id=resource_id,
    )

    db.add(event)

    return event
