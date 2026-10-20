"""
API endpoint tests for Sentry integration routes (/api/sentry/*).
Validates HTTP response codes, error translations, payload structures,
and confirms token is never exposed in API responses.
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.app.schemas.sentry import (
    SentryStatusResponse,
    SentryRateLimit,
    SentryProject,
    SentryIssue,
    SentryEvent,
    SentryException,
    SentryStackFrame,
    SentryTag,
    SentryEvidence,
)
from backend.app.services.sentry_service import (
    SentryError,
    SentryConfigError,
    SentryAuthError,
    SentryPermissionError,
    SentryRateLimitError,
    SentryNotFoundError,
    SentryUnavailableError,
)

ORG = "test-org"
PROJECT = "test-project"


def test_api_sentry_status_operational(client):
    mock_status = SentryStatusResponse(
        configured=True,
        authenticated=True,
        reachable=True,
        org_slug=ORG,
        project_slug=PROJECT,
        base_url="https://sentry.io",
        rate_limit=SentryRateLimit(limit=60, remaining=58, reset_at=1700000000, concurrent=5),
        message="Sentry integration operational",
    )

    with patch("backend.app.api.routes.sentry.sentry_service.get_status", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_status
        response = client.get("/api/sentry/status")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert data["authenticated"] is True
    assert data["reachable"] is True
    assert data["org_slug"] == ORG
    assert data["project_slug"] == PROJECT
    assert data["rate_limit"]["remaining"] == 58
    assert "token" not in data
    assert "SENTRY_AUTH_TOKEN" not in response.text


def test_api_sentry_status_unconfigured(client):
    mock_status = SentryStatusResponse(
        configured=False,
        authenticated=False,
        reachable=False,
        org_slug=None,
        project_slug=None,
        base_url="https://sentry.io",
        message="Sentry org or project slug is not configured.",
    )

    with patch("backend.app.api.routes.sentry.sentry_service.get_status", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_status
        response = client.get("/api/sentry/status")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["reachable"] is False


def test_api_sentry_project_success(client):
    mock_project = SentryProject(
        id="12345",
        slug=PROJECT,
        name="Test Project",
        organization_slug=ORG,
        platform="python-fastapi",
        is_active=True,
        has_access=True,
    )

    with patch("backend.app.api.routes.sentry.sentry_service.get_project", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_project
        response = client.get("/api/sentry/project")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "12345"
    assert data["slug"] == PROJECT
    assert data["platform"] == "python-fastapi"


def test_api_sentry_project_errors(client):
    error_cases = [
        (SentryAuthError("Invalid auth token"), 401),
        (SentryPermissionError("Access denied"), 403),
        (SentryNotFoundError("Project not found"), 404),
        (SentryRateLimitError("Rate limit exceeded"), 429),
        (SentryUnavailableError("Sentry unreachable"), 503),
        (SentryConfigError("Missing configuration"), 503),
        (SentryError("Unexpected error"), 502),
    ]

    for err, expected_status in error_cases:
        with patch("backend.app.api.routes.sentry.sentry_service.get_project", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = err
            response = client.get("/api/sentry/project")
            assert response.status_code == expected_status, f"Expected {expected_status} for {type(err)}, got {response.status_code}"


def test_api_sentry_issues_success(client):
    mock_issues = [
        SentryIssue(
            id="101",
            short_id="TEST-1",
            title="DatabaseConnectionTimeout",
            culprit="backend.database.pool",
            permalink="https://sentry.io/organizations/test-org/issues/101/",
            logger="backend",
            level="error",
            status="unresolved",
            count=15,
            user_count=3,
            first_seen="2026-10-19T10:00:00Z",
            last_seen="2026-10-19T11:00:00Z",
            metadata={"type": "DatabaseConnectionTimeout", "value": "Connection pool exhausted"},
        )
    ]

    with patch("backend.app.api.routes.sentry.sentry_service.get_issues", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_issues
        response = client.get("/api/sentry/issues?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "101"
    assert data[0]["title"] == "DatabaseConnectionTimeout"
    assert data[0]["count"] == 15


def test_api_sentry_issue_details_success(client):
    mock_issue = SentryIssue(
        id="101",
        short_id="TEST-1",
        title="ValueError: Invalid token",
        culprit="backend.auth",
        permalink="https://sentry.io/organizations/test-org/issues/101/",
        logger="backend",
        level="error",
        status="unresolved",
        count=1,
        user_count=1,
        first_seen="2026-10-19T10:00:00Z",
        last_seen="2026-10-19T11:00:00Z",
    )

    with patch("backend.app.api.routes.sentry.sentry_service.get_issue", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_issue
        response = client.get("/api/sentry/issues/101")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "101"
    assert data["title"] == "ValueError: Invalid token"


def test_api_sentry_issue_details_not_found(client):
    with patch("backend.app.api.routes.sentry.sentry_service.get_issue", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = SentryNotFoundError("Issue 999 not found")
        response = client.get("/api/sentry/issues/999")

    assert response.status_code == 404


def test_api_sentry_issue_events_success(client):
    mock_events = [
        SentryEvent(
            id="evt_1001",
            event_id="evt_abc123",
            issue_id="101",
            title="DatabaseConnectionTimeout",
            message="Connection pool exhausted after 30s",
            platform="python",
            timestamp="2026-10-19T10:00:00Z",
            tags=[SentryTag(key="environment", value="production"), SentryTag(key="release", value="v1.2.0")],
            release="v1.2.0",
            dist=None,
            user=None,
            exceptions=[
                SentryException(
                    type="DatabaseConnectionTimeout",
                    value="Connection pool exhausted after 30s",
                    module="backend.database.pool",
                    frames=[
                        SentryStackFrame(
                            filename="pool.py",
                            function="acquire_connection",
                            module="backend.database.pool",
                            lineno=45,
                            context_line="raise DatabaseConnectionTimeout()",
                            in_app=True,
                        )
                    ],
                )
            ],
        )
    ]

    with patch("backend.app.api.routes.sentry.sentry_service.get_issue_events", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_events
        response = client.get("/api/sentry/issues/101/events")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_id"] == "evt_abc123"
    assert len(data[0]["exceptions"]) == 1
    assert data[0]["exceptions"][0]["frames"][0]["filename"] == "pool.py"


def test_api_sentry_evidence_success(client):
    mock_evidence = SentryEvidence(
        status="CONNECTED",
        org_slug=ORG,
        project_slug=PROJECT,
        issue_count=1,
        issues=[],
        matched_exception_type="DatabaseConnectionTimeout",
        matched_exception_value="Connection pool exhausted",
        matched_stack_trace_frames=[
            SentryStackFrame(
                filename="backend/database/pool.py",
                function="acquire",
                module="backend.database.pool",
                lineno=50,
                in_app=True,
            )
        ],
        correlated_release="v1.2.0",
        correlated_environment="production",
        message="Sentry identified 1 active issue(s).",
    )

    with patch("backend.app.api.routes.sentry.sentry_service.get_runtime_evidence", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_evidence
        response = client.get("/api/sentry/evidence")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONNECTED"
    assert data["issue_count"] == 1
    assert data["matched_exception_type"] == "DatabaseConnectionTimeout"
    assert len(data["matched_stack_trace_frames"]) == 1
