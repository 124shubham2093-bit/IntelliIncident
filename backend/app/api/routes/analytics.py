import os
import json
from typing import List
from fastapi import APIRouter

from backend.app.schemas.analytics import MLMetrics, FeatureImportance
from backend.app.core.config import settings
from backend.app.ml.severity_classifier import SeverityClassifier

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/ml", tags=["ML Analytics"])
severity_classifier = SeverityClassifier()

def load_metadata():
    meta_path = os.path.join(settings.MODELS_DIR, "model_metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None

@router.get("/metrics", response_model=MLMetrics)
async def get_metrics():
    meta = load_metadata()
    if meta and "metrics" in meta:
        return meta["metrics"]

    raise HTTPException(
        status_code=503,
        detail="Trained model metrics are unavailable. Models must be trained using 'python backend/ml_training/train_models.py' first."
    )

@router.get("/features", response_model=List[FeatureImportance])
async def get_features():
    meta = load_metadata()
    if meta and "featureImportance" in meta:
        return meta["featureImportance"]

    try:
        return severity_classifier.get_feature_importances()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
