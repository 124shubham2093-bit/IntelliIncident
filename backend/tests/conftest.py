import os
import sys
import tempfile
import sqlite3
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.db.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db(tmp_path_factory):
    # Create isolated temporary database path for tests
    test_db_dir = tmp_path_factory.mktemp("test_db")
    test_db_path = str(test_db_dir / "test_intelli_incident.db")
    original_db_path = settings.SQLITE_DB_PATH
    settings.SQLITE_DB_PATH = test_db_path

    # Initialize isolated test schema
    init_db()

    # Seed isolated fixture record INC-8610 into test db only
    conn = sqlite3.connect(test_db_path)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO incidents (
        id, title, service, severity, risk, risk_score,
        anomaly_detected, anomaly_score, status, timestamp,
        summary, affected_users_count, root_cause_category
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "INC-8610", "Order Processing Service Degradation", "order-processing-service",
        "CRITICAL", "MEDIUM", 59, 0, 0.0027, "INVESTIGATING",
        "2026-09-26T14:30:00Z", "Elevated error rate post-deployment", 800, "DEPLOYMENT"
    ))
    cur.execute("""
    INSERT INTO incident_metrics (
        incident_id, service, affected_users, error_rate,
        latency_p99, latency_p50, request_volume,
        deployment_recency_minutes, cpu_utilization,
        memory_utilization, service_criticality
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "INC-8610", "order-processing-service", 800, 42.19,
        514.3, 120.0, 8200, 102, 42.0, 58.0, 3
    ))
    cur.execute("""
    INSERT INTO deployments (
        id, service, commit_hash, deployed_at, environment, status, author, changelog
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "DEP-8610", "order-processing-service", "a1b2c3d", "2026-09-26T12:48:00Z", "production", "SUCCESS", "release-bot", "Deploy v2.4.1"
    ))
    cur.execute("""
    INSERT INTO runtime_logs (
        id, incident_id, timestamp, log_level, message, stack_trace
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "LOG-8610", "INC-8610", "2026-09-26T14:31:00Z", "ERROR", "NullPointerException in order serializer", "at OrderService.java:42"
    ))
    cur.execute("""
    INSERT INTO support_tickets (
        id, incident_id, created_at, customer_tier, subject, sentiment
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "TCK-8610", "INC-8610", "2026-09-26T14:32:00Z", "Tier 1", "Orders failing at checkout", "NEGATIVE"
    ))
    cur.execute("""
    INSERT INTO evidence_events (
        id, incident_id, timestamp, event_type, service, description, severity
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "EVT-8610", "INC-8610", "2026-09-26T14:30:00Z", "MONITORING_ALERT", "order-processing-service", "Error rate exceeded 40%", "CRITICAL"
    ))
    conn.commit()
    conn.close()

    yield

    settings.SQLITE_DB_PATH = original_db_path

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
