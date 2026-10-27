
from backend.app.models.encounter import Encounter


def detect_encounter_gaps(
    encounter: Encounter,
) -> list[dict]:
    """
    Detect data-readiness and explicitly documented
    follow-up gaps in a hospital encounter.

    No clinical diagnosis or treatment decisions.
    """

    gaps = []

    features = encounter.normalized_features or {}

    # -----------------------------------------
    # 1. Pending data quality review
    # -----------------------------------------

    if encounter.data_quality_status == "pending_review":
        gaps.append({
            "code": "DATA_REVIEW_PENDING",
            "category": "data_quality",
            "severity": "medium",
            "description": (
                "Encounter data is awaiting quality review."
            ),
            "recommendation": (
                "Review and validate the encounter record."
            ),
        })

    # -----------------------------------------
    # 2. Missing admission date
    # -----------------------------------------

    if encounter.admission_date is None:
        gaps.append({
            "code": "ADMISSION_DATE_MISSING",
            "category": "data_quality",
            "severity": "medium",
            "description": (
                "Admission date is not recorded."
            ),
            "recommendation": (
                "Verify the admission date from "
                "the source record."
            ),
        })

    # -----------------------------------------
    # 3. Missing discharge date
    # Only flag when discharge is explicitly
    # marked as confirmed.
    # -----------------------------------------

    if (
        features.get("discharge_confirmed") is True
        and encounter.discharge_date is None
    ):
        gaps.append({
            "code": "DISCHARGE_DATE_MISSING",
            "category": "data_quality",
            "severity": "medium",
            "description": (
                "Discharge is confirmed but the "
                "discharge date is missing."
            ),
            "recommendation": (
                "Verify and record the discharge date."
            ),
        })

    # -----------------------------------------
    # 4. Follow-up scheduling gap
    # Only when explicitly documented.
    # -----------------------------------------

    if (
        features.get("follow_up_required") is True
        and features.get("follow_up_scheduled") is False
    ):
        gaps.append({
            "code": "FOLLOW_UP_NOT_SCHEDULED",
            "category": "follow_up",
            "severity": "high",
            "description": (
                "A required follow-up is explicitly "
                "recorded as not scheduled."
            ),
            "recommendation": (
                "Ask the responsible care team "
                "to review follow-up scheduling."
            ),
        })

    return gaps
