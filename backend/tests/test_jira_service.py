"""
Unit tests for JiraService (Jira Work Item and Incident Ticket Integration).
All tests mock the HTTP/network layer using AsyncMock/httpx and require no real Jira instance.
STRICTLY SAFE: No real credentials or tokens are used.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from backend.app.services.jira_service import JiraService, _extract_adf_text
from backend.app.schemas.jira import (
    JiraStatusResponse,
    JiraIssue,
    JiraEvidence,
    JiraCorrelationMatch,
)


def test_extract_adf_text():
    # String passthrough
    assert _extract_adf_text("Simple text description") == "Simple text description"
    assert _extract_adf_text(None) == ""

    # Atlassian Document Format (ADF) dictionary
    adf_doc = {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "High latency observed on"},
                    {"type": "text", "text": "order-service checkout API."},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Root cause: pool exhaustion."},
                ],
            },
        ],
    }
    extracted = _extract_adf_text(adf_doc)
    assert "High latency observed on" in extracted
    assert "order-service checkout API." in extracted
    assert "pool exhaustion" in extracted


@pytest.mark.anyio
async def test_jira_service_init_defaults(monkeypatch):
    monkeypatch.setattr("backend.app.services.jira_service.settings.JIRA_BASE_URL", "https://intelli.atlassian.net")
    monkeypatch.setattr("backend.app.services.jira_service.settings.JIRA_EMAIL", "dev@intelliincident.org")
    monkeypatch.setattr("backend.app.services.jira_service.settings.JIRA_API_TOKEN", "mock_dummy_token_123")
    monkeypatch.setattr("backend.app.services.jira_service.settings.JIRA_PROJECT_KEY", "OPS")

    service = JiraService()
    assert service.base_url == "https://intelli.atlassian.net"
    assert service.email == "dev@intelliincident.org"
    assert service.project_key == "OPS"
    assert service.timeout == 4.0
    assert service.is_configured() is True


@pytest.mark.anyio
async def test_jira_service_unconfigured():
    service = JiraService(base_url="", email="", api_token="")
    assert service.is_configured() is False

    status = await service.get_health()
    assert status.configured is False
    assert status.authenticated is False
    assert status.reachable is False
    assert "not configured" in status.message.lower()


@pytest.mark.anyio
async def test_jira_service_health_connected():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "displayName": "DevOps Engineer",
        "emailAddress": "engineer@intelliincident.org",
        "active": True,
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = JiraService(
        base_url="https://mock.atlassian.net",
        email="engineer@intelliincident.org",
        api_token="mock_dummy_token",
        project_key="INC",
        client=mock_client,
    )
    status = await service.get_health()

    assert status.configured is True
    assert status.authenticated is True
    assert status.reachable is True
    assert status.user_display_name == "DevOps Engineer"
    assert status.project_key == "INC"
    assert "verified" in status.message.lower()


@pytest.mark.anyio
async def test_jira_service_health_auth_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 401

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = JiraService(
        base_url="https://mock.atlassian.net",
        email="engineer@intelliincident.org",
        api_token="invalid_token",
        client=mock_client,
    )
    status = await service.get_health()

    assert status.configured is True
    assert status.authenticated is False
    assert status.reachable is True
    assert "authentication failed" in status.message.lower()


@pytest.mark.anyio
async def test_jira_service_health_unavailable():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    service = JiraService(
        base_url="https://down.atlassian.net",
        email="dev@test.org",
        api_token="token",
        client=mock_client,
    )
    status = await service.get_health()

    assert status.configured is True
    assert status.authenticated is False
    assert status.reachable is False
    assert "cannot reach" in status.message.lower()


@pytest.mark.anyio
async def test_jira_service_health_timeout():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Read timed out"))

    service = JiraService(
        base_url="https://slow.atlassian.net",
        email="dev@test.org",
        api_token="token",
        client=mock_client,
    )
    status = await service.get_health()

    assert status.configured is True
    assert status.authenticated is False
    assert status.reachable is False
    assert "timed out" in status.message.lower()


@pytest.mark.anyio
async def test_jira_service_get_issues_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "issues": [
            {
                "id": "10001",
                "key": "OPS-42",
                "fields": {
                    "summary": "Database connection pool saturated under peak checkout load",
                    "description": "HikariCP pool timeout thrown in checkout-service",
                    "issuetype": {"name": "Incident"},
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Critical"},
                    "project": {"key": "OPS", "name": "Operations"},
                    "labels": ["checkout-service", "database", "p1"],
                    "components": [{"name": "CheckoutBackend"}],
                    "assignee": {"displayName": "SRE OnCall"},
                    "reporter": {"displayName": "Automated Alert"},
                    "created": "2026-05-10T14:18:00Z",
                    "updated": "2026-05-10T14:25:00Z",
                },
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = JiraService(
        base_url="https://mock.atlassian.net",
        email="dev@test.org",
        api_token="dummy_token",
        client=mock_client,
    )

    issues = await service.get_issues("project = 'OPS'", limit=10)
    assert len(issues) == 1
    iss = issues[0]
    assert iss.key == "OPS-42"
    assert iss.issue_type == "Incident"
    assert iss.status == "In Progress"
    assert iss.priority == "Critical"
    assert "checkout-service" in iss.labels
    assert iss.assignee == "SRE OnCall"
    assert iss.url == "https://mock.atlassian.net/browse/OPS-42"


@pytest.mark.anyio
async def test_jira_service_get_issue_single():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "10002",
        "key": "OPS-99",
        "fields": {
            "summary": "NullPointerException in payment gateway serialization",
            "description": "Unhandled exception thrown in PaymentController",
            "issuetype": {"name": "Bug"},
            "status": {"name": "Open"},
            "priority": {"name": "High"},
        },
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = JiraService(
        base_url="https://mock.atlassian.net",
        email="dev@test.org",
        api_token="dummy_token",
        client=mock_client,
    )

    issue = await service.get_issue("OPS-99")
    assert issue is not None
    assert issue.key == "OPS-99"
    assert issue.summary == "NullPointerException in payment gateway serialization"
    assert issue.issue_type == "Bug"


@pytest.mark.anyio
async def test_jira_service_get_issue_not_found():
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = JiraService(
        base_url="https://mock.atlassian.net",
        email="dev@test.org",
        api_token="dummy_token",
        client=mock_client,
    )

    issue = await service.get_issue("NONEXISTENT-999")
    assert issue is None


def test_jira_service_correlation_exact_id():
    service = JiraService()
    issue = JiraIssue(
        id="101",
        key="INC-55",
        summary="Customer reports 500 error during checkout for incident INC-8610",
        description="Linked to incident INC-8610 in production",
        labels=["INC-8610", "checkout"],
    )

    score, matched_by, explanation = service.calculate_correlation(
        issue=issue,
        incident_id="INC-8610",
        service="checkout-service",
    )

    assert score >= 0.60
    assert "incident_id" in matched_by
    assert "INC-8610" in explanation


def test_jira_service_correlation_service_match():
    service = JiraService()
    issue = JiraIssue(
        id="102",
        key="PROJ-200",
        summary="Slow response times reported on payment-service",
        description="P99 latency degradation",
        labels=["payment-service", "latency"],
    )

    score, matched_by, explanation = service.calculate_correlation(
        issue=issue,
        incident_id="INC-9999",
        service="payment-service",
    )

    assert score >= 0.35
    assert "service_name" in matched_by
    assert "payment-service" in explanation


def test_jira_service_correlation_irrelevant_issue():
    service = JiraService()
    issue = JiraIssue(
        id="103",
        key="HR-10",
        summary="Update annual leave policy documentation",
        description="HR handbook review",
        labels=["documentation"],
    )

    score, matched_by, explanation = service.calculate_correlation(
        issue=issue,
        incident_id="INC-8610",
        service="auth-service",
    )

    assert score < 0.20
    assert len(matched_by) == 0


@pytest.mark.anyio
async def test_get_incident_jira_evidence_unconfigured():
    service = JiraService(base_url="", email="", api_token="")
    evidence = await service.get_incident_jira_evidence(service="order-service")

    assert evidence.status == "NOT_CONFIGURED"
    assert evidence.total_issues_found == 0
    assert evidence.primary_issue is None
    assert evidence.correlation_strength == "NONE"


@pytest.mark.anyio
async def test_get_incident_jira_evidence_connected():
    mock_myself_resp = MagicMock(status_code=200, json=lambda: {"displayName": "SRE User"})
    mock_search_resp = MagicMock(
        status_code=200,
        json=lambda: {
            "issues": [
                {
                    "id": "20001",
                    "key": "OPS-303",
                    "fields": {
                        "summary": "Critical connection pool timeout on checkout-service INC-7700",
                        "description": "Database queries failing across all pods",
                        "issuetype": {"name": "Incident"},
                        "status": {"name": "Under Investigation"},
                        "priority": {"name": "Highest"},
                        "labels": ["checkout-service", "INC-7700"],
                    },
                }
            ]
        },
    )

    async def mock_get(url, **kwargs):
        if "myself" in url:
            return mock_myself_resp
        return mock_search_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=mock_get)

    service = JiraService(
        base_url="https://test.atlassian.net",
        email="sre@test.org",
        api_token="dummy_token",
        project_key="OPS",
        client=mock_client,
    )

    evidence = await service.get_incident_jira_evidence(
        service="checkout-service",
        incident_id="INC-7700",
        title="Checkout failure spike",
    )

    assert evidence.status == "CONNECTED"
    assert evidence.primary_issue is not None
    assert evidence.primary_issue.key == "OPS-303"
    assert evidence.correlation_strength in ("HIGH", "MEDIUM")
    assert evidence.correlation is not None
    assert "incident_id" in evidence.correlation.matched_by
