"""
API endpoint tests for Prometheus metric intelligence routes (/api/prometheus/*).
Validates HTTP responses, error translations, safe status reporting, and evidence retrieval.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.app.schemas.prometheus import (
    PrometheusStatusResponse,
    PrometheusEvidence,
    PrometheusMetricSample,
    PrometheusTimeWindow,
)
from backend.app.db.database import get_db_connection


def test_api_prometheus_health_connected(client):
    mock_status = PrometheusStatusResponse(
        status="CONNECTED",
        url="http://prometheus.test:9090",
        reachable=True,
        version="2.45.0",
        message="Prometheus operational",
    )

    with patch("backend.app.api.routes.prometheus.prometheus_service.get_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = mock_status
        response = client.get("/api/prometheus/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONNECTED"
    assert data["reachable"] is True
    assert data["version"] == "2.45.0"
    assert "url" in data


def test_api_prometheus_health_unavailable(client):
    mock_status = PrometheusStatusResponse(
        status="UNAVAILABLE",
        url="http://prometheus.test:9090",
        reachable=False,
        version=None,
        message="Prometheus unreachable",
    )

    with patch("backend.app.api.routes.prometheus.prometheus_service.get_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = mock_status
        response = client.get("/api/prometheus/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNAVAILABLE"
    assert data["reachable"] is False


def test_api_prometheus_metrics(client):
    with patch("backend.app.api.routes.prometheus.prometheus_service.query_instant", new_callable=AsyncMock) as mock_q:
        mock_q.return_value = 45.2
        response = client.get("/api/prometheus/metrics?service=checkout-service")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "cpu_utilization" in data
    assert data["cpu_utilization"] == 45.2


def test_api_prometheus_evidence_not_found(client):
    response = client.get("/api/prometheus/evidence/DOES-NOT-EXIST-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_prometheus_evidence_success(client):
    # Insert test incident into db
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO incidents (
        id, title, service, severity, risk, risk_score,
        anomaly_detected, anomaly_score, status, timestamp, summary,
        affected_users_count, root_cause_category
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "INC-PROM-TEST-1", "Prometheus Latency Spike", "payment-service",
        "HIGH", "HIGH", 85.0, 1, 0.92, "INVESTIGATING", "2026-05-10T14:30:00Z", "Test summary",
        150, "CODE_ERROR"
    ))
    conn.commit()
    conn.close()

    mock_evidence = PrometheusEvidence(
        status="CONNECTED",
        url="http://prom.test:9090",
        service="payment-service",
        time_window=PrometheusTimeWindow(
            incident_time="2026-05-10T14:30:00Z",
            baseline_start="2026-05-10T13:30:00Z",
            baseline_end="2026-05-10T14:15:00Z",
            incident_start="2026-05-10T14:15:00Z",
            incident_end="2026-05-10T15:00:00Z",
        ),
        cpu_utilization=PrometheusMetricSample(
            metric_name="CPU Utilization",
            query="rate(container_cpu_usage_seconds_total[5m])",
            unit="%",
            baseline_value=30.0,
            observed_value=85.0,
            deviation_pct=183.3,
            anomaly_detected=True,
            correlation_strength="HIGH",
            status="AVAILABLE",
        ),
        anomalies_detected=1,
        highest_correlation="HIGH",
        summary="1 anomalous metric deviation detected: CPU Utilization (+183.3%).",
    )

    with patch("backend.app.api.routes.prometheus.prometheus_service.get_incident_metric_evidence", new_callable=AsyncMock) as mock_get_ev:
        mock_get_ev.return_value = mock_evidence
        response = client.get("/api/prometheus/evidence/INC-PROM-TEST-1")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONNECTED"
    assert data["service"] == "payment-service"
    assert data["anomalies_detected"] == 1
    assert data["highest_correlation"] == "HIGH"
    assert data["cpu_utilization"]["anomaly_detected"] is True
