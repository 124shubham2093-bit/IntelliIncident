import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal, Optional

from backend.app.core.config import settings

router = APIRouter(tags=["Health"])

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    service: str
    version: Optional[str] = "1.0.0"
    mlEngineReady: Optional[bool] = True
    fuzzyEngineReady: Optional[bool] = True

@router.get("/health", response_model=HealthResponse)
async def check_health():
    iso_exists = os.path.exists(os.path.join(settings.MODELS_DIR, "isolation_forest.joblib"))
    rf_exists = os.path.exists(os.path.join(settings.MODELS_DIR, "severity_classifier.joblib"))
    db_exists = os.path.exists(settings.SQLITE_DB_PATH)

    ml_ready = iso_exists and rf_exists
    fuzzy_ready = True

    overall_status = "ok" if (ml_ready and db_exists) else "degraded"

    return {
        "status": overall_status,
        "service": "intelli-incident-backend",
        "version": settings.VERSION,
        "mlEngineReady": ml_ready,
        "fuzzyEngineReady": fuzzy_ready,
    }
