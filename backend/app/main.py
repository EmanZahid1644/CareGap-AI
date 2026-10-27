
from fastapi import FastAPI

import backend.app.models.patient

from backend.app.api.organizations import router as organizations_router
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.memberships import router as memberships_router
from backend.app.api.patients import router as patients_router
from backend.app.api.encounters import router as encounters_router
from backend.app.api.encounter_imports import router as encounter_imports_router
from backend.app.api.clinical_analytics import (
    router as clinical_analytics_router,
)
from backend.app.api.readmission_risk import (
    router as readmission_risk_router,
)
from backend.app.api.care_gaps import (
    router as care_gaps_router,
)

app = FastAPI(
    title="CareGap-AI API",
    description="Healthcare intelligence and follow-up workflow platform.",
    version="0.1.0",
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "name": "CareGap-AI",
        "message": "Healthcare intelligence API is running.",
        "version": "0.1.0",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "caregap-ai-api",
    }


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(memberships_router)
app.include_router(organizations_router)
app.include_router(patients_router)
app.include_router(encounters_router)
app.include_router(encounter_imports_router)
app.include_router(clinical_analytics_router)
app.include_router(readmission_risk_router)
app.include_router(care_gaps_router)