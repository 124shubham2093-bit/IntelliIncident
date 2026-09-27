"""
Isolation Forest Anomaly Detection Engine for IntelliIncident
Uses scikit-learn's IsolationForest to detect telemetry outliers.
"""

import os
import joblib
import datetime
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.app.ml.feature_engineering import extract_features, FEATURE_COLUMNS
from backend.app.core.config import settings

MODEL_FILE = os.path.join(settings.MODELS_DIR, "isolation_forest.joblib")

class AnomalyDetector:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_FILE
        self.model: Optional[IsolationForest] = None
        self.threshold: float = 0.0 # IsolationForest decision_function threshold: negative is anomaly
        self.baseline_means: Dict[str, float] = {}
        self.load_model()

    def load_model(self) -> bool:
        if os.path.exists(self.model_path):
            try:
                payload = joblib.load(self.model_path)
                if isinstance(payload, dict):
                    self.model = payload.get("model")
                    self.threshold = payload.get("threshold", 0.0)
                    self.baseline_means = payload.get("baseline_means", {})
                else:
                    self.model = payload
                return True
            except Exception as e:
                print(f"Error loading Isolation Forest model: {e}")
                return False
        return False

    def predict(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run anomaly detection on telemetry inputs.
        Returns AnomalyResult conforming to frontend TypeScript contract.
        """
        features_df = extract_features(telemetry_data)

        if self.model is None:
            raise RuntimeError(
                f"Isolation Forest model artifact is unavailable at '{self.model_path}'. "
                "Trained model artifact is required for genuine anomaly detection."
            )

        raw_score = float(self.model.decision_function(features_df)[0])
        # Decision function: negative values indicate anomalies, positive indicate normal instances
        is_anomaly = raw_score < self.threshold

        # Determine significant deviations from baseline
        deviations = []
        for feat in ["error_rate", "latency_p99", "cpu_utilization", "request_volume"]:
            if feat in features_df.columns and feat in self.baseline_means:
                current_val = float(features_df[feat].iloc[0])
                base_val = float(self.baseline_means[feat])
                if base_val > 0 and current_val > base_val * 1.5:
                    ratio = (current_val / base_val) - 1.0
                    deviations.append(f"{feat.replace('_', ' ').title()} +{ratio*100:.0f}% vs baseline")

        observed_dev_str = "; ".join(deviations) if deviations else ("Nominal operational limits" if not is_anomaly else "Multivariate anomaly signature")

        return {
            "detected": is_anomaly,
            "score": round(raw_score, 4),
            "threshold": round(self.threshold, 4),
            "model": "Isolation Forest",
            "featuresAnalyzed": FEATURE_COLUMNS,
            "evaluatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "baselineMean": round(float(self.baseline_means.get("error_rate", 2.0)), 2),
            "observedDeviation": observed_dev_str,
        }
