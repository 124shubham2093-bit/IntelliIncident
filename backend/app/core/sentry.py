"""
Sentry Error Monitoring SDK Initialization & Utilities for FastAPI.
Provides safe, clean initialization of the official Python Sentry SDK.
Separates application error monitoring (reporting) from SentryService (REST evidence reading).
"""

import logging
from typing import Optional, Dict, Any
import sentry_sdk

from backend.app.core.config import settings

logger = logging.getLogger("intelliincident.sentry_sdk")


def init_sentry() -> bool:
    """
    Initializes the Sentry Python SDK for FastAPI application error monitoring.
    Configured strictly for error reporting (traces_sample_rate=0.0).
    Never prints or logs DSN or auth tokens.
    Returns True if initialized, False if unconfigured or skipped.
    """
    dsn = settings.SENTRY_DSN
    if not dsn or not dsn.strip():
        logger.info("Sentry SDK not initialized: SENTRY_DSN is not configured.")
        return False

    try:
        sentry_sdk.init(
            dsn=dsn.strip(),
            environment=settings.ENVIRONMENT,
            release=f"{settings.PROJECT_NAME}@{settings.VERSION}",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        )
        logger.info("Sentry SDK initialized successfully for FastAPI error monitoring.")
        return True
    except Exception as exc:
        logger.warning("Failed to initialize Sentry SDK: %s", str(exc))
        return False


def is_sentry_sdk_active() -> bool:
    """Check if the Sentry SDK has an active Hub / Client initialized."""
    try:
        if hasattr(sentry_sdk, "is_initialized"):
            return bool(sentry_sdk.is_initialized())
        client = sentry_sdk.get_client()
        return bool(client and client.is_active())
    except Exception:
        return False


def trigger_controlled_sentry_error(unhandled: bool = False) -> Dict[str, Any]:
    """
    Safe development-only mechanism to generate exactly one controlled test exception.
    Captures a deterministic exception without fabricating responses or affecting production.
    """
    if settings.ENVIRONMENT.lower() in ("production", "prod"):
        raise PermissionError("Controlled Sentry test errors cannot be triggered in production.")

    test_message = "IntelliIncident Sentry Verification: Controlled test exception"

    if unhandled:
        # Intentionally raised for middleware-level unhandled exception capture
        raise RuntimeError(test_message)

    try:
        raise RuntimeError(test_message)
    except RuntimeError as exc:
        event_id = sentry_sdk.capture_exception(exc)
        try:
            sentry_sdk.flush(timeout=2.0)
        except Exception:
            pass

        return {
            "status": "triggered",
            "message": "Controlled Sentry test exception generated and captured by Sentry SDK.",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "sentry_event_id": str(event_id) if event_id else None,
            "sdk_initialized": is_sentry_sdk_active(),
            "environment": settings.ENVIRONMENT,
        }
