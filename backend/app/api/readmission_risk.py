
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import joblib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.dependencies import (
    require_organization_permission,
)
from backend.app.core.permissions import Permission
from backend.app.ml.readmission_features import (
    ReadmissionFeatures,
)


router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/analytics",
    tags=["Readmission Risk - Demo"],
)

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml"
    / "artifacts"
    / "readmission_demo.joblib"
)


class ReadmissionRiskResponse(BaseModel):
    organization_id: UUID
    risk_score: float = Field(ge=0, le=1)
    risk_percentage: float = Field(ge=0, le=100)
    model_version: str
    model_type: str
    disclaimer: str


@lru_cache(maxsize=1)
def load_demo_model():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            "Demo model has not been trained."
        )

    # Only load artifacts created by our own
    # trusted training script.
    artifact = joblib.load(MODEL_PATH)

    if artifact.get("data_source") != "synthetic":
        raise ValueError(
            "Unexpected model artifact source."
        )

    if artifact.get("feature_columns") != [
        "age",
        "prior_admissions",
        "length_of_stay",
        "diabetes",
    ]:
        raise ValueError(
            "Unexpected model feature schema."
        )

    return artifact


@router.post(
    "/readmission-risk",
    response_model=ReadmissionRiskResponse,
)
def predict_readmission_risk(
    organization_id: UUID,
    features: ReadmissionFeatures,
    membership=Depends(
        require_organization_permission(
            Permission.CLINICAL_READ
        )
    ),
):
    """
    Return a synthetic-demo model prediction.

    No patient data is stored by this endpoint.
    This is not clinical decision support.
    """

    try:
        artifact = load_demo_model()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Demo ML model is not available.",
        )

    model = artifact["model"]

    feature_vector = [
        [
            features.age,
            features.prior_admissions,
            features.length_of_stay,
            int(features.diabetes),
        ]
    ]

    probability = float(
        model.predict_proba(feature_vector)[0][1]
    )

    return ReadmissionRiskResponse(
        organization_id=organization_id,
        risk_score=round(probability, 4),
        risk_percentage=round(
            probability * 100,
            2,
        ),
        model_version=artifact["model_version"],
        model_type="synthetic_demo",
        disclaimer=(
            "Synthetic demonstration only. "
            "This score is not clinically validated "
            "and must not guide patient care."
        ),
    )
