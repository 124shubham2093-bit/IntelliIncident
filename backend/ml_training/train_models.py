"""
Model Training Pipeline for IntelliIncident
Trains Isolation Forest and Random Forest on generated dataset.
Evaluates and outputs true performance metrics without artificial adjustments.
"""

import os
import sys
import json
import datetime
import joblib
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from backend.app.core.config import settings
from backend.app.ml.feature_engineering import extract_features, FEATURE_COLUMNS, FEATURE_METADATA

CLASSES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

def train_and_evaluate():
    data_dir = settings.DATA_DIR
    models_dir = settings.MODELS_DIR
    os.makedirs(models_dir, exist_ok=True)

    # 1. Load data
    incidents_path = os.path.join(data_dir, "incidents.csv")
    metrics_path = os.path.join(data_dir, "monitoring_metrics.csv")

    if not os.path.exists(incidents_path) or not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Datasets not found in {data_dir}. Run generate_dataset.py first.")

    df_incidents = pd.read_csv(incidents_path)
    df_metrics = pd.read_csv(metrics_path)

    # Merge features with labels
    merged = pd.merge(df_incidents, df_metrics, left_on="id", right_on="incident_id", suffixes=("", "_metric"))

    # Feature extraction (guaranteed target leakage prevention)
    X = extract_features(merged)
    y = merged["severity"]

    print(f"Total dataset size: {len(X)} samples with {X.shape[1]} engineered features.")

    # 2. Train-test split (80% train, 20% test, stratified by severity)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"Training set: {len(X_train)} samples, Test set: {len(X_test)} samples.")

    # 3. Train Isolation Forest for Anomaly Detection
    # Unsupervised: fit on telemetry features
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.18,
        random_state=42,
        n_jobs=-1,
    )
    iso_forest.fit(X_train)

    # Compute baseline feature means for anomaly explanation
    baseline_means = X_train.mean().to_dict()

    # Save Isolation Forest model payload
    iso_payload = {
        "model": iso_forest,
        "threshold": 0.0,
        "baseline_means": baseline_means,
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "feature_names": FEATURE_COLUMNS,
    }
    iso_path = os.path.join(models_dir, "isolation_forest.joblib")
    joblib.dump(iso_payload, iso_path)
    print(f"Isolation Forest model saved to: {iso_path}")

    # 4. Train Random Forest for Multiclass Severity Classification
    rf_classifier = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf_classifier.fit(X_train, y_train)

    # 5. Evaluate on Test Set
    y_pred = rf_classifier.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=CLASSES)
    confusion_matrix_data = []
    for i, actual_cls in enumerate(CLASSES):
        confusion_matrix_data.append({
            "actual": actual_cls,
            "low": int(cm[i][0]),
            "medium": int(cm[i][1]),
            "high": int(cm[i][2]),
            "critical": int(cm[i][3]),
        })

    # Feature Importances (Gini)
    importances = rf_classifier.feature_importances_
    feature_importances = []
    for feat_meta, imp in zip(FEATURE_METADATA, importances):
        feature_importances.append({
            "feature": feat_meta["displayName"],
            "importance": round(float(imp), 4),
            "category": feat_meta["category"],
        })
    feature_importances.sort(key=lambda x: x["importance"], reverse=True)

    # Save Random Forest model payload
    rf_payload = {
        "model": rf_classifier,
        "classes": CLASSES,
        "feature_importances": feature_importances,
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "feature_names": FEATURE_COLUMNS,
    }
    rf_path = os.path.join(models_dir, "severity_classifier.joblib")
    joblib.dump(rf_payload, rf_path)
    print(f"Random Forest model saved to: {rf_path}")

    # Anomaly score distribution for dashboard analytics
    decision_scores = iso_forest.decision_function(X_test)
    bins = [
        {"bin": "-0.8 to -0.6", "min": -0.8, "max": -0.6, "scoreRange": "Severe Anomaly"},
        {"bin": "-0.6 to -0.4", "min": -0.6, "max": -0.4, "scoreRange": "High Anomaly"},
        {"bin": "-0.4 to -0.2", "min": -0.4, "max": -0.2, "scoreRange": "Borderline"},
        {"bin": "-0.2 to 0.0", "min": -0.2, "max": 0.0, "scoreRange": "Mild Inlier"},
        {"bin": "0.0 to 0.2", "min": 0.0, "max": 0.2, "scoreRange": "Normal"},
        {"bin": "0.2 to 0.4", "min": 0.2, "max": 0.4, "scoreRange": "Normal"},
        {"bin": "0.4 to 0.6", "min": 0.4, "max": 0.6, "scoreRange": "Nominal Baseline"},
    ]
    anomaly_distribution = []
    for b in bins:
        count = int(np.sum((decision_scores >= b["min"]) & (decision_scores < b["max"])))
        anomaly_distribution.append({
            "bin": b["bin"],
            "normalCount": count if b["min"] >= 0 else 0,
            "anomalyCount": count if b["max"] <= 0 else 0,
            "scoreRange": b["scoreRange"],
        })

    # Save metadata JSON
    metadata = {
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec_macro, 4),
            "recall": round(rec_macro, 4),
            "f1Score": round(f1_macro, 4),
            "trainingSamplesCount": len(X_train),
            "lastTrainedDate": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "featureImportance": feature_importances,
        "confusionMatrix": confusion_matrix_data,
        "anomalyDistribution": anomaly_distribution,
    }

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Model metadata saved to: {metadata_path}")

    # Print Report
    print("\n" + "="*50)
    print("MODEL EVALUATION RESULTS (Actual Test Set Metrics)")
    print("="*50)
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec_macro:.4f} (Macro)")
    print(f"Recall:    {rec_macro:.4f} (Macro)")
    print(f"Macro F1:  {f1_macro:.4f}")
    print("\nConfusion Matrix:")
    for row in confusion_matrix_data:
        print(f"  Actual {row['actual']:8s} -> Low: {row['low']:3d}, Medium: {row['medium']:3d}, High: {row['high']:3d}, Critical: {row['critical']:3d}")
    print("\nTop 5 Feature Importances:")
    for fi in feature_importances[:5]:
        print(f"  - {fi['feature']} ({fi['category']}): {fi['importance']:.4f}")
    print("="*50 + "\n")

    return metadata

if __name__ == "__main__":
    train_and_evaluate()
