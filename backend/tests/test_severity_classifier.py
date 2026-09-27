import pytest
from backend.app.ml.severity_classifier import SeverityClassifier

def test_severity_classifier_prediction_structure():
    classifier = SeverityClassifier()
    data = {
        "error_rate": 5.0,
        "latency_p99": 200.0,
        "latency_p50": 50.0,
        "affected_users": 150,
        "cpu_utilization": 45.0,
        "memory_utilization": 50.0,
        "deployment_recency_minutes": 120,
        "request_volume": 3000,
        "service_criticality": 3,
    }
    result = classifier.predict(data)
    assert result["predictedSeverity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["model"] == "Random Forest"

    probs = result["classProbabilities"]
    assert "low" in probs
    assert "medium" in probs
    assert "high" in probs
    assert "critical" in probs
    total_prob = sum(probs.values())
    assert pytest.approx(total_prob, abs=0.05) == 1.0

def test_feature_importances():
    classifier = SeverityClassifier()
    importances = classifier.get_feature_importances()
    assert len(importances) > 0
    for fi in importances:
        assert "feature" in fi
        assert "importance" in fi
        assert "category" in fi
        assert fi["importance"] >= 0.0

def test_severity_classifier_model_unavailable():
    classifier = SeverityClassifier(model_path="nonexistent_path/fake_model.joblib")
    with pytest.raises(RuntimeError, match="Random Forest model artifact is unavailable"):
        classifier.predict({"error_rate": 1.0})
    with pytest.raises(RuntimeError, match="Random Forest model metadata or artifact is unavailable"):
        classifier.get_feature_importances()
