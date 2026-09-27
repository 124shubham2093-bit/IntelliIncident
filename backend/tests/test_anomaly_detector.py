import pytest
from backend.app.ml.anomaly_detector import AnomalyDetector

def test_anomaly_detector_nominal_telemetry():
    detector = AnomalyDetector()
    nominal_data = {
        "error_rate": 0.5,
        "latency_p99": 110.0,
        "latency_p50": 35.0,
        "affected_users": 10,
        "cpu_utilization": 25.0,
        "memory_utilization": 30.0,
        "deployment_recency_minutes": 300,
        "request_volume": 2000,
        "service_criticality": 3,
    }
    result = detector.predict(nominal_data)
    assert "detected" in result
    assert "score" in result
    assert "threshold" in result
    assert result["model"] == "Isolation Forest"
    assert len(result["featuresAnalyzed"]) == 12
    # Nominal case should yield positive decision function (inlier)
    assert result["score"] >= result["threshold"]
    assert result["detected"] is False

def test_anomaly_detector_extreme_telemetry():
    detector = AnomalyDetector()
    extreme_data = {
        "error_rate": 45.0,
        "latency_p99": 3200.0,
        "latency_p50": 600.0,
        "affected_users": 35000,
        "cpu_utilization": 98.0,
        "memory_utilization": 96.0,
        "deployment_recency_minutes": 5,
        "request_volume": 12000,
        "service_criticality": 5,
    }
    result = detector.predict(extreme_data)
    assert result["detected"] is True
    assert result["score"] < result["threshold"]
    assert "observedDeviation" in result

def test_anomaly_detector_model_unavailable():
    detector = AnomalyDetector(model_path="nonexistent_path/fake_model.joblib")
    with pytest.raises(RuntimeError, match="Isolation Forest model artifact is unavailable"):
        detector.predict({"error_rate": 1.0})
