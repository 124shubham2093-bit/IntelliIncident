"""
Tests for PaymentGateway Telemetry Producer Service (scripts/payment_gateway_service.py).
Validates healthz, normal charge processing, Prometheus metrics emission,
controlled fault mode injection, and fault reset.
"""

import pytest
from starlette.testclient import TestClient
from scripts.payment_gateway_service import app, fault_state


@pytest.fixture(autouse=True)
def reset_fault_fixture():
    # Ensure fault is cleared before and after each test
    fault_state["active"] = False
    fault_state["latency_seconds"] = 0.0  # Instant for unit tests
    yield
    fault_state["active"] = False


def test_payment_gateway_healthz():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "PaymentGateway"
    assert data["fault_active"] is False


def test_payment_gateway_normal_charge_flow():
    client = TestClient(app)
    resp = client.post("/api/charge", json={"amount": 49.99, "currency": "USD"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["amount"] == 49.99

    # Verify metrics endpoint contains recorded request
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics_text = metrics_resp.text
    assert "http_requests_total" in metrics_text
    assert 'service="PaymentGateway"' in metrics_text
    assert 'status="200"' in metrics_text
    assert "http_request_duration_seconds" in metrics_text


def test_payment_gateway_fault_injection():
    client = TestClient(app)

    # 1. Trigger fault mode
    trigger_resp = client.post("/fault/trigger", json={"active": True, "latency_seconds": 0.01})
    assert trigger_resp.status_code == 200
    assert trigger_resp.json()["fault_active"] is True

    # 2. Charge request should now fail with HTTP 500
    fail_resp = client.post("/api/charge", json={"amount": 100.0})
    assert fail_resp.status_code == 500
    assert "DB_CONNECTION_TIMEOUT" in fail_resp.text

    # 3. Metrics should contain status="500"
    metrics_resp = client.get("/metrics")
    metrics_text = metrics_resp.text
    assert 'status="500"' in metrics_text

    # 4. Reset fault mode
    reset_resp = client.post("/fault/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["fault_active"] is False

    # 5. Subsequent charge succeeds with HTTP 200
    success_resp = client.post("/api/charge", json={"amount": 25.0})
    assert success_resp.status_code == 200
