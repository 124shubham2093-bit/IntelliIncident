"""
Unit tests for Sentry Python SDK integration and error monitoring in FastAPI.
Tests ensure deterministic execution without external network calls or live credentials.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.sentry import (
    init_sentry,
    is_sentry_sdk_active,
    trigger_controlled_sentry_error,
)


def test_sentry_sdk_init_unconfigured(monkeypatch):
    """Verify SDK does not initialize when SENTRY_DSN is None/empty."""
    monkeypatch.setattr(settings, "SENTRY_DSN", None)
    with patch("backend.app.core.sentry.sentry_sdk.init") as mock_init:
        res = init_sentry()
        assert res is False
        mock_init.assert_not_called()


def test_sentry_sdk_init_configured(monkeypatch):
    """Verify SDK initializes with correct parameters when SENTRY_DSN is present."""
    fake_dsn = "https://public_key@sentry.example.com/12345"
    monkeypatch.setattr(settings, "SENTRY_DSN", fake_dsn)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.0)

    with patch("backend.app.core.sentry.sentry_sdk.init") as mock_init:
        res = init_sentry()
        assert res is True
        mock_init.assert_called_once()
        _, kwargs = mock_init.call_args
        assert kwargs["dsn"] == fake_dsn
        assert kwargs["environment"] == "staging"
        assert kwargs["traces_sample_rate"] == 0.0
        assert "IntelliIncident" in kwargs["release"]


def test_trigger_controlled_sentry_error_dev(monkeypatch):
    """Verify development-only controlled exception generation."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    with patch("backend.app.core.sentry.sentry_sdk.capture_exception") as mock_capture:
        mock_capture.return_value = "fake_event_id_123"
        result = trigger_controlled_sentry_error(unhandled=False)

        assert result["status"] == "triggered"
        assert result["exception_type"] == "RuntimeError"
        assert "IntelliIncident Sentry Verification" in result["exception_message"]
        assert result["sentry_event_id"] == "fake_event_id_123"
        mock_capture.assert_called_once()


def test_trigger_controlled_sentry_error_prod_forbidden(monkeypatch):
    """Verify controlled exception generation is strictly forbidden in production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(PermissionError) as exc_info:
        trigger_controlled_sentry_error(unhandled=False)

    assert "cannot be triggered in production" in str(exc_info.value)


def test_api_sentry_debug_trigger_error_dev(client, monkeypatch):
    """Test POST /api/sentry/debug/trigger-error in development mode."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    with patch("backend.app.core.sentry.sentry_sdk.capture_exception") as mock_capture:
        mock_capture.return_value = "test_event_999"
        response = client.post("/api/sentry/debug/trigger-error?unhandled=false")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["exception_type"] == "RuntimeError"
    assert data["sentry_event_id"] == "test_event_999"


def test_api_sentry_debug_trigger_error_prod_forbidden(client, monkeypatch):
    """Test POST /api/sentry/debug/trigger-error is blocked with 403 in production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    response = client.post("/api/sentry/debug/trigger-error")
    assert response.status_code == 403
    assert "forbidden in production" in response.json()["detail"].lower()


def test_api_sentry_debug_trigger_error_unhandled(client, monkeypatch):
    """Test POST /api/sentry/debug/trigger-error with unhandled=true raises exception."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    with pytest.raises(RuntimeError) as exc_info:
        client.post("/api/sentry/debug/trigger-error?unhandled=true")

    assert "IntelliIncident Sentry Verification" in str(exc_info.value)
