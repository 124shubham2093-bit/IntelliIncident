"""
Random Forest Severity Classification Engine for IntelliIncident
Multiclass prediction of incident severity (LOW, MEDIUM, HIGH, CRITICAL)
with calibrated probabilities and feature importance extraction.
"""

import os
import joblib
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from backend.app.ml.feature_engineering import extract_features, FEATURE_COLUMNS, FEATURE_METADATA
from backend.app.core.config import settings

MODEL_FILE = os.path.join(settings.MODELS_DIR, "severity_classifier.joblib")
CLASSES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

class SeverityClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_FILE
        self.model: Optional[RandomForestClassifier] = None
        self.feature_importances: List[Dict[str, Any]] = []
        self.classes: List[str] = CLASSES
        self.load_model()

    def load_model(self) -> bool:
        if os.path.exists(self.model_path):
            try:
                payload = joblib.load(self.model_path)
                if isinstance(payload, dict):
                    self.model = payload.get("model")
                    self.classes = payload.get("classes", CLASSES)
                    self.feature_importances = payload.get("feature_importances", [])
                else:
                    self.model = payload
                return True
            except Exception as e:
                print(f"Error loading Random Forest model: {e}")
                return False
        return False

    def predict(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict incident severity and probability distribution.
        Returns SeverityPrediction conforming to frontend contract.
        """
        features_df = extract_features(telemetry_data)

        if self.model is None:
            raise RuntimeError(
                f"Random Forest model artifact is unavailable at '{self.model_path}'. "
                "Trained model artifact is required for genuine severity classification."
            )

        # Model prediction
        pred_idx = self.model.predict(features_df)[0]
        # Check if pred_idx is integer or string
        if isinstance(pred_idx, (int, np.integer)):
            predicted_severity = self.classes[pred_idx]
        else:
            predicted_severity = str(pred_idx)

        # Probabilities
        proba = self.model.predict_proba(features_df)[0]
        probs_dict = {}
        for idx, cls_name in enumerate(self.model.classes_):
            cls_lower = str(cls_name).lower()
            probs_dict[cls_lower] = round(float(proba[idx]), 3)

        # Ensure all 4 classes present in probabilities
        for c in ["low", "medium", "high", "critical"]:
            if c not in probs_dict:
                probs_dict[c] = 0.0

        confidence = probs_dict.get(predicted_severity.lower(), float(max(proba)))

        return {
            "predictedSeverity": predicted_severity,
            "confidence": round(float(confidence), 3),
            "model": "Random Forest",
            "classProbabilities": probs_dict,
        }

    def get_feature_importances(self) -> List[Dict[str, Any]]:
        if self.feature_importances:
            return self.feature_importances

        if self.model and hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            ranked = []
            for feat_meta, imp in zip(FEATURE_METADATA, importances):
                ranked.append({
                    "feature": feat_meta["displayName"],
                    "importance": round(float(imp), 3),
                    "category": feat_meta["category"],
                })
            ranked.sort(key=lambda x: x["importance"], reverse=True)
            return ranked

        raise RuntimeError(
            f"Random Forest model metadata or artifact is unavailable at '{self.model_path}'. "
            "Trained model artifact is required to report genuine feature importances."
        )
