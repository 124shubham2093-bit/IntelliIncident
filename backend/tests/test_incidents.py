import sqlite3
import os
from fastapi.testclient import TestClient
from backend.app.core.config import settings
from backend.app.main import app


def test_empty_runtime_database_on_disk():
    """Verify that the actual application runtime SQLite database contains 0 incident rows."""
    real_db_path = os.path.join(settings.DATA_DIR, "intelli_incident.db")
    assert os.path.exists(real_db_path)
    conn = sqlite3.connect(real_db_path)
    c = conn.cursor()
    incidents_count = c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    metrics_count = c.execute("SELECT COUNT(*) FROM incident_metrics").fetchone()[0]
    conn.close()
    assert incidents_count == 0
    assert metrics_count == 0

def test_get_incidents_empty_database(monkeypatch, tmp_path):
    """Verify that GET /api/incidents returns [] when the database is empty."""
    from backend.app.db.database import init_db
    empty_db = str(tmp_path / "empty_runtime.db")
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", empty_db)
    init_db()
    with TestClient(app) as empty_client:
        res = empty_client.get("/api/incidents")
        assert res.status_code == 200
        assert res.json() == []


def test_list_incidents(client):
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert isinstance(incidents, list)
    assert len(incidents) > 0
    first = incidents[0]
    assert "id" in first
    assert "title" in first
    assert "severity" in first
    assert "risk" in first
    assert "riskScore" in first
    assert "anomalyDetected" in first
    assert "anomalyScore" in first
    assert "status" in first
    assert "affectedUsersCount" in first

def test_filter_incidents_by_severity(client):
    response = client.get("/api/incidents?severity=CRITICAL")
    assert response.status_code == 200
    incidents = response.json()
    for inc in incidents:
        assert inc["severity"] == "CRITICAL"

def test_filter_incidents_by_service(client):
    response = client.get("/api/incidents?service=order-processing-service")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) > 0
    for inc in incidents:
        assert inc["service"] == "order-processing-service"

def test_get_incident_by_id(client):
    list_res = client.get("/api/incidents")
    first_id = list_res.json()[0]["id"]

    response = client.get(f"/api/incidents/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_id
    assert "metrics" in data
    assert "mlAnalysis" in data
    assert "fuzzyRisk" in data
    assert "evidenceTimeline" in data
    assert "rootCauseCandidates" in data
    assert "recommendations" in data

def test_get_nonexistent_incident(client):
    response = client.get("/api/incidents/INC-NONEXISTENT")
    assert response.status_code == 404

def test_create_and_ingest_incident_pipeline(client):
    """
    Test POST /api/incidents:
    Ingest a new operational incident, run end-to-end pipeline
    (Feature extraction -> Isolation Forest -> Random Forest -> Fuzzy Risk -> RCA),
    persist, and retrieve it.
    """
    payload = {
        "id": "INC-TEST-9999",
        "title": "Payment Microservice Connection Timeout Spike",
        "service": "payment-gateway",
        "summary": "Sudden connection timeout cascade after configuration change",
        "status": "OPEN",
        "affected_users_count": 1200,
        "metrics": {
            "error_rate": 35.5,
            "latency_p99": 1650.0,
            "latency_p50": 210.0,
            "affected_users": 1200,
            "request_volume": 4500,
            "deployment_recency_minutes": 20,
            "cpu_utilization": 82.0,
            "memory_utilization": 88.0,
            "service_criticality": 5
        },
        "logs": [
            {
                "log_level": "ERROR",
                "message": "Connection pool exhausted to payment upstream host",
                "stack_trace": "TimeoutException at ConnectionPool.borrow():118"
            }
        ],
        "deployments": [
            {
                "commit_hash": "c8d9e0f",
                "environment": "production",
                "status": "SUCCESS",
                "author": "devops-lead",
                "changelog": "Tune threadpool and connection limits"
            }
        ],
        "tickets": [
            {
                "customer_tier": "Enterprise",
                "subject": "Payment checkout failing with 504",
                "sentiment": "NEGATIVE"
            }
        ],
        "events": [
            {
                "event_type": "MONITORING_ALERT",
                "service": "payment-gateway",
                "description": "Error rate exceeded 30% SLA threshold",
                "severity": "CRITICAL"
            }
        ]
    }

    # 1. Post to ingestion endpoint
    create_res = client.post("/api/incidents", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()

    assert created_data["id"] == "INC-TEST-9999"
    assert created_data["service"] == "payment-gateway"
    assert "metrics" in created_data
    assert created_data["metrics"]["errorRate"] == 35.5

    # Verify ML Analysis was executed
    assert "mlAnalysis" in created_data
    assert "anomaly" in created_data["mlAnalysis"]
    assert "detected" in created_data["mlAnalysis"]["anomaly"]
    assert "severityPrediction" in created_data["mlAnalysis"]
    assert created_data["mlAnalysis"]["severityPrediction"]["predictedSeverity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Verify Fuzzy Risk Assessment was executed
    assert "fuzzyRisk" in created_data
    assert 0 <= created_data["fuzzyRisk"]["riskScore"] <= 100
    assert created_data["fuzzyRisk"]["riskLevel"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "VERY_HIGH"]

    # Verify Root Cause Analysis and Recommendations
    assert len(created_data["rootCauseCandidates"]) > 0
    assert len(created_data["recommendations"]) > 0

    # 2. Verify retrieval via GET /api/incidents/INC-TEST-9999
    get_res = client.get("/api/incidents/INC-TEST-9999")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()
    assert retrieved_data["id"] == "INC-TEST-9999"
    assert retrieved_data["title"] == "Payment Microservice Connection Timeout Spike"

