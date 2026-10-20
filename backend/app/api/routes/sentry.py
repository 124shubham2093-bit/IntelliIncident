"""
Sentry Runtime Error Intelligence API Routes for IntelliIncident.
Exposes endpoints for verifying Sentry configuration, project status,
retrieving issues and events, and fetching normalized runtime error evidence.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.core.config import settings
from backend.app.schemas.sentry import (
    SentryStatusResponse,
    SentryProject,
    SentryIssue,
    SentryEvent,
    SentryEvidence,
)
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

router = APIRouter(prefix="/sentry", tags=["Sentry"])
sentry_service = SentryService()


@router.get("/status", response_model=SentryStatusResponse)
async def get_sentry_status():
    """
    Check configuration, API reachability, and rate limit status of the Sentry integration.
    Safe endpoint that never crashes and never exposes SENTRY_AUTH_TOKEN.
    """
    try:
        return await sentry_service.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to check Sentry status: {str(e)}",
        )


@router.get("/project", response_model=SentryProject)
async def get_project_info():
    """
    Retrieve configured Sentry project metadata.
    """
    try:
        return await sentry_service.get_project()
    except SentryAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except SentryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except SentryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SentryRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (SentryConfigError, SentryUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except SentryError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/issues", response_model=List[SentryIssue])
async def list_issues(
    query: Optional[str] = Query(default="is:unresolved", description="Sentry search filter query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of issues to return"),
):
    """
    List runtime error issues for the configured project.
    """
    try:
        return await sentry_service.get_issues(query=query, limit=limit)
    except SentryAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except SentryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except SentryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SentryRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (SentryConfigError, SentryUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except SentryError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/issues/{issue_id}", response_model=SentryIssue)
async def get_issue_details(issue_id: str):
    """
    Retrieve details for a single Sentry issue by issue ID.
    """
    try:
        return await sentry_service.get_issue(issue_id=issue_id)
    except SentryAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except SentryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except SentryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SentryRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (SentryConfigError, SentryUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except SentryError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/issues/{issue_id}/events", response_model=List[SentryEvent])
async def get_issue_events(
    issue_id: str,
    limit: int = Query(default=5, ge=1, le=20, description="Maximum number of events to return"),
):
    """
    Retrieve events and stack traces for a Sentry issue.
    """
    try:
        return await sentry_service.get_issue_events(issue_id=issue_id, limit=limit)
    except SentryAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except SentryPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except SentryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SentryRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (SentryConfigError, SentryUnavailableError) as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except SentryError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/evidence", response_model=SentryEvidence)
async def get_sentry_evidence(
    service: Optional[str] = Query(default=None, description="Service name filter"),
    environment: Optional[str] = Query(default=None, description="Environment filter (e.g. production)"),
    release: Optional[str] = Query(default=None, description="Release/revision tag filter"),
    limit: int = Query(default=5, ge=1, le=20, description="Max issues to analyze"),
):
    """
    Fetch normalized Sentry runtime error evidence for incident correlation and root cause analysis.
    Returns a safe SentryEvidence payload even if unconfigured or remote errors occur.
    """
    return await sentry_service.get_runtime_evidence(
        service=service,
        environment=environment,
        release=release,
        limit=limit,
    )


@router.post("/debug/trigger-error", response_model=Dict[str, Any])
async def trigger_test_sentry_error(
    unhandled: bool = Query(
        default=False,
        description="Whether to raise unhandled exception for middleware-level capture",
    ),
):
    """
    Safe development-only test mechanism to generate exactly one controlled Sentry exception.
    Captures a deterministic exception to verify Sentry error monitoring.
    Strictly forbidden and disabled in production environments.
    """
    if settings.ENVIRONMENT.lower() in ("production", "prod"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Controlled Sentry test errors are strictly forbidden in production.",
        )

    try:
        from backend.app.core.sentry import trigger_controlled_sentry_error
        return trigger_controlled_sentry_error(unhandled=unhandled)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except RuntimeError as exc:
        if unhandled:
            # Re-raise to trigger unhandled exception handling by Sentry ASGI middleware
            raise
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
