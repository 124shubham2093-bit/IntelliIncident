"""
API endpoint tests for Jira work item intelligence routes (/api/jira/*).
Validates HTTP responses, error translations, safe status reporting, and evidence retrieval.
STRICTLY SAFE: No real credentials or tokens are tested.
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.app.schemas.jira import (
    JiraStatusResponse,
    JiraIssue,
    JiraEvidence,
    JiraCorrelationMatch,
)
from backend.app.db.database import get_db_connection


def test_api_jira_health_connected(client):
    mock_status = JiraStatusResponse(
        configured=True,
        authenticated=True,
        reachable=True,
        base_url="https://mock.atlassian.net",
        email="sre@test.org",
        project_key="OPS",
        user_display_name="DevOps Lead",
        message="Jira connection verified and user authenticated successfully.",
    )

    with patch("backend.app.api.routes.jira.jira_service.get_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = mock_status
        response = client.get("/api/jira/health")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert data["authenticated"] is True
    assert data["reachable"] is True
    assert data["user_display_name"] == "DevOps Lead"
    assert "token" not in data
    assert "api_token" not in data


def test_api_jira_health_unconfigured(client):
    mock_status = JiraStatusResponse(
        configured=False,
        authenticated=False,
        reachable=False,
        base_url="",
        message="Jira base URL is not configured.",
    )

    with patch("backend.app.api.routes.jira.jira_service.get_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = mock_status
        response = client.get("/api/jira/health")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["reachable"] is False


def test_api_jira_issues(client):
    mock_issues = [
        JiraIssue(
            id="101",
            key="OPS-101",
            summary="Payment service timeout spike",
            issue_type="Incident",
            status="In Progress",
            priority="High",
            labels=["payment-service", "p1"],
            url="https://mock.atlassian.net/browse/OPS-101",
        )
    ]

    with patch("backend.app.api.routes.jira.jira_service.get_issues", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_issues
        response = client.get("/api/jira/issues?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["key"] == "OPS-101"
    assert data[0]["summary"] == "Payment service timeout spike"


def test_api_jira_issue_detail_success(client):
    mock_issue = JiraIssue(
        id="102",
        key="OPS-102",
        summary="Deadlock in order placement transaction",
        description="Database lock wait timeout exceeded",
        issue_type="Bug",
        status="Open",
        priority="Critical",
    )

    with patch("backend.app.api.routes.jira.jira_service.get_issue", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_issue
        response = client.get("/api/jira/issues/OPS-102")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "OPS-102"
    assert data["priority"] == "Critical"


def test_api_jira_issue_detail_not_found(client):
    with patch("backend.app.api.routes.jira.jira_service.get_issue", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get("/api/jira/issues/UNKNOWN-999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_jira_evidence_not_found(client):
    response = client.get("/api/jira/evidence/DOES-NOT-EXIST-888")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_jira_evidence_success(client):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO incidents (
        id, title, service, severity, risk, risk_score,
        anomaly_detected, anomaly_score, status, timestamp, summary,
        affected_users_count, root_cause_category
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "INC-JIRA-TEST-1", "Checkout Latency Surge", "checkout-service",
        "HIGH", "HIGH", 85.0, 1, 0.90, "INVESTIGATING", "2026-05-10T14:30:00Z", "Test summary",
        200, "DATABASE"
    ))
    conn.commit()
    conn.close()

    mock_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        matched_issues=[
            JiraIssue(
                id="301",
                key="OPS-301",
                summary="Database connection pool saturated under peak checkout load",
                issue_type="Incident",
                status="Investigating",
                priority="Critical",
                labels=["checkout-service", "INC-JIRA-TEST-1"],
            )
        ],
        primary_issue=JiraIssue(
            id="301",
            key="OPS-301",
            summary="Database connection pool saturated under peak checkout load",
            issue_type="Incident",
            status="Investigating",
            priority="Critical",
            labels=["checkout-service", "INC-JIRA-TEST-1"],
        ),
        correlation=JiraCorrelationMatch(
            matched_by=["incident_id", "service_name"],
            confidence_score=0.95,
            explanation="ticket explicitly cites incident ID 'INC-JIRA-TEST-1'; ticket is scoped to affected service 'checkout-service'",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira issue OPS-301 with high confidence.",
    )

    with patch("backend.app.api.routes.jira.jira_service.get_incident_jira_evidence", new_callable=AsyncMock) as mock_ev:
        mock_ev.return_value = mock_evidence
        response = client.get("/api/jira/evidence/INC-JIRA-TEST-1")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONNECTED"
    assert data["correlation_strength"] == "HIGH"
    assert data["primary_issue"]["key"] == "OPS-301"
    assert data["correlation"]["confidence_score"] == 0.95
