"""
Unit tests for SentryService (READ-ONLY Sentry REST API Integration).
All tests mock the HTTP/network layer and require no real Sentry credentials.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from backend.app.services.sentry_service import (
    SentryService,
    SentryError,
    SentryConfigError,
    SentryAuthError,
    SentryPermissionError,
    SentryRateLimitError,
    SentryNotFoundError,
    SentryUnavailableError,
)
from backend.app.schemas.sentry import (
    SentryStatusResponse,
    SentryProject,
    SentryIssue,
    SentryEvent,
    SentryEvidence,
)


@pytest.mark.anyio
async def test_service_init_defaults(monkeypatch):
    monkeypatch.setattr("backend.app.services.sentry_service.settings.SENTRY_BASE_URL", "https://sentry.io")
    service = SentryService()
    assert service.base_url == "https://sentry.io"
    assert service.timeout == 4.0


@pytest.mark.anyio
async def test_service_unconfigured_status():
    service = SentryService(auth_token=None, org_slug=None, project_slug=None)
    status = await service.get_status()
    assert status.configured is False
    assert status.reachable is False
    assert status.authenticated is False
    assert "not configured" in status.message.lower()


@pytest.mark.anyio
async def test_service_missing_token_status():
    service = SentryService(auth_token=None, org_slug="my-org", project_slug="my-project")
    status = await service.get_status()
    assert status.configured is True
    assert status.authenticated is False
    assert status.reachable is False
    assert "auth token is missing" in status.message.lower()


@pytest.mark.anyio
async def test_get_status_operational():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "x-sentry-rate-limit-remaining": "95",
        "x-sentry-rate-limit-reset": "1730000000",
    }
    mock_resp.json.return_value = {
        "id": "12345",
        "slug": "payment-api",
        "name": "Payment API",
        "platform": "python",
    }

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="test_sentry_token_abc123",
        org_slug="test-org",
        project_slug="payment-api",
        client=mock_client,
    )
    status = await service.get_status()
    assert status.configured is True
    assert status.authenticated is True
    assert status.reachable is True
    assert status.org_slug == "test-org"
    assert status.project_slug == "payment-api"
    assert status.rate_limit is not None
    assert status.rate_limit.remaining == 95
    assert "operational" in status.message.lower()


@pytest.mark.anyio
async def test_get_status_auth_error_401():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {}
    mock_resp.json.return_value = {"detail": "Invalid token"}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="invalid_token",
        org_slug="test-org",
        project_slug="payment-api",
        client=mock_client,
    )
    status = await service.get_status()
    assert status.configured is True
    assert status.authenticated is False
    assert status.reachable is True
    assert "authentication failed" in status.message.lower()


@pytest.mark.anyio
async def test_get_status_permission_error_403():
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {}
    mock_resp.json.return_value = {"detail": "You do not have permission to perform this action."}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="token_without_perms",
        org_slug="test-org",
        project_slug="payment-api",
        client=mock_client,
    )
    status = await service.get_status()
    assert status.configured is True
    assert status.reachable is True
    assert "permission" in status.message.lower()


@pytest.mark.anyio
async def test_get_status_not_found_404():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    mock_resp.json.return_value = {"detail": "The requested resource does not exist"}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="valid_token",
        org_slug="test-org",
        project_slug="nonexistent-project",
        client=mock_client,
    )
    status = await service.get_status()
    assert status.configured is True
    assert status.reachable is True
    assert "not found" in status.message.lower()


@pytest.mark.anyio
async def test_get_status_rate_limit_429():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"retry-after": "45"}
    mock_resp.json.return_value = {"detail": "Rate limit exceeded"}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="valid_token",
        org_slug="test-org",
        project_slug="payment-api",
        client=mock_client,
    )
    status = await service.get_status()
    assert status.configured is True
    assert "rate limit" in status.message.lower()


@pytest.mark.anyio
async def test_get_status_unreachable_network_error():
    mock_client = AsyncMock()
    mock_client.request.side_effect = httpx.ConnectError("Connection refused")

    service = SentryService(
        auth_token="valid_token",
        org_slug="test-org",
        project_slug="payment-api",
        client=mock_client,
    )
    status = await service.get_status()
    assert status.configured is True
    assert status.reachable is False
    assert "unreachable" in status.message.lower()


@pytest.mark.anyio
async def test_get_project_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {
        "id": "98765",
        "slug": "checkout-service",
        "name": "Checkout Service",
        "platform": "python-fastapi",
        "status": "active",
        "isPublic": False,
        "dateCreated": "2026-01-15T10:00:00Z",
    }
    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="test_token",
        org_slug="fintech-org",
        project_slug="checkout-service",
        client=mock_client,
    )
    project = await service.get_project()
    assert isinstance(project, SentryProject)
    assert project.id == "98765"
    assert project.slug == "checkout-service"
    assert project.name == "Checkout Service"
    assert project.platform == "python-fastapi"


@pytest.mark.anyio
async def test_get_issues_normalization():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = [
        {
            "id": "1001",
            "shortId": "CHECKOUT-1A",
            "title": "ValueError: Unsupported currency EUR in transaction",
            "culprit": "backend/services/payment.py in process_transaction",
            "type": "error",
            "level": "error",
            "count": 42,
            "userCount": 18,
            "firstSeen": "2026-10-19T08:00:00Z",
            "lastSeen": "2026-10-19T08:30:00Z",
            "permalink": "https://sentry.io/organizations/fintech-org/issues/1001/",
            "status": "unresolved",
            "metadata": {
                "type": "ValueError",
                "value": "Unsupported currency EUR in transaction",
            },
        }
    ]
    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="test_token",
        org_slug="fintech-org",
        project_slug="checkout-service",
        client=mock_client,
    )
    issues = await service.get_issues(query="is:unresolved", limit=5)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, SentryIssue)
    assert issue.id == "1001"
    assert issue.short_id == "CHECKOUT-1A"
    assert issue.count == 42
    assert issue.metadata["type"] == "ValueError"


@pytest.mark.anyio
async def test_get_issue_events_with_stack_frames():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = [
        {
            "id": "evt-999",
            "eventID": "abc123def456",
            "title": "ValueError: Unsupported currency",
            "dateCreated": "2026-10-19T08:29:00Z",
            "platform": "python",
            "environment": "production",
            "release": {"version": "v1.4.2", "shortVersion": "1.4.2"},
            "tags": [
                {"key": "environment", "value": "production"},
                {"key": "server_name", "value": "node-prod-01"},
            ],
            "entries": [
                {
                    "type": "exception",
                    "data": {
                        "values": [
                            {
                                "type": "ValueError",
                                "value": "Unsupported currency",
                                "module": "backend.services.payment",
                                "stacktrace": {
                                    "frames": [
                                        {
                                            "filename": "backend/app/main.py",
                                            "absPath": "/app/backend/app/main.py",
                                            "function": "checkout_endpoint",
                                            "lineNo": 45,
                                            "inApp": True,
                                        },
                                        {
                                            "filename": "backend/services/payment.py",
                                            "absPath": "/app/backend/services/payment.py",
                                            "function": "process_transaction",
                                            "lineNo": 28,
                                            "inApp": True,
                                        },
                                    ]
                                },
                            }
                        ]
                    },
                }
            ],
        }
    ]
    mock_client = AsyncMock()
    mock_client.request.return_value = mock_resp

    service = SentryService(
        auth_token="test_token",
        org_slug="fintech-org",
        project_slug="checkout-service",
        client=mock_client,
    )
    events = await service.get_issue_events("1001", limit=1)
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, SentryEvent)
    assert event.environment == "production"
    assert event.release == "v1.4.2"
    assert len(event.exceptions) == 1
    exc = event.exceptions[0]
    assert exc.type == "ValueError"
    assert len(exc.frames) == 2
    assert exc.frames[1].filename == "backend/services/payment.py"
    assert exc.frames[1].lineno == 28


@pytest.mark.anyio
async def test_get_runtime_evidence_connected():
    issues_resp = MagicMock()
    issues_resp.status_code = 200
    issues_resp.headers = {}
    issues_resp.json.return_value = [
        {
            "id": "1001",
            "title": "KeyError: 'session_token'",
            "culprit": "auth/session.py in get_session",
            "count": 5,
            "metadata": {"type": "KeyError", "value": "'session_token'"},
        }
    ]

    event_resp = MagicMock()
    event_resp.status_code = 200
    event_resp.headers = {}
    event_resp.json.return_value = {
        "id": "evt-111",
        "eventID": "evt-111",
        "title": "KeyError: 'session_token'",
        "environment": "production",
        "release": "a1b2c3d",
        "entries": [
            {
                "type": "exception",
                "data": {
                    "values": [
                        {
                            "type": "KeyError",
                            "value": "'session_token'",
                            "stacktrace": {
                                "frames": [
                                    {
                                        "filename": "src/auth/session.py",
                                        "lineNo": 88,
                                        "function": "get_session",
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ],
    }

    mock_client = AsyncMock()
    def fake_request(method, url, **kwargs):
        if "/issues/1001/events/latest/" in url:
            return event_resp
        return issues_resp

    mock_client.request.side_effect = fake_request

    service = SentryService(
        auth_token="valid_token",
        org_slug="my-org",
        project_slug="auth-service",
        client=mock_client,
    )
    evidence = await service.get_runtime_evidence(service="auth-service", environment="production")
    assert isinstance(evidence, SentryEvidence)
    assert evidence.status == "CONNECTED"
    assert evidence.issue_count == 1
    assert evidence.matched_exception_type == "KeyError"
    assert len(evidence.matched_stack_trace_frames) == 1
    assert evidence.matched_stack_trace_frames[0].filename == "src/auth/session.py"
    assert evidence.correlated_release == "a1b2c3d"


@pytest.mark.anyio
async def test_get_runtime_evidence_unconfigured():
    service = SentryService(auth_token=None, org_slug=None, project_slug=None)
    evidence = await service.get_runtime_evidence()
    assert evidence.status == "NOT_CONFIGURED"
    assert evidence.issue_count == 0


@pytest.mark.anyio
async def test_token_header_security():
    token = "secret_sentry_token_xyz"
    service = SentryService(auth_token=token)
    headers = service._get_headers()
    assert headers["Authorization"] == f"Bearer {token}"
    # Verify str() or status never exposes token
    status = await service.get_status()
    status_str = str(status.model_dump())
    assert token not in status_str
