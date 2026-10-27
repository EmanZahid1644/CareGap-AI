from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health")
def versioned_health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "caregap-ai-api",
        "version": "v1",
    }