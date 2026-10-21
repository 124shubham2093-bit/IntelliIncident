"""
Jira Work Item and Incident Ticket Intelligence API Routes for IntelliIncident.
Exposes endpoints for verifying Jira connectivity, querying work items,
and retrieving incident-scoped Jira ticket evidence for RCA.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.jira import (
    JiraStatusResponse,
    JiraIssue,
    JiraEvidence,
)
from backend.app.services.jira_service import JiraService
from backend.app.db.database import get_db_connection

router = APIRouter(prefix="/jira", tags=["Jira"])
jira_service = JiraService()


@router.get("/health", response_model=JiraStatusResponse)
async def get_jira_health():
    """
    Check connectivity, API reachability, and authentication status of Jira.
    Safe endpoint that never crashes even if Jira is unconfigured or unreachable.
    """
    return await jira_service.get_health()


@router.get("/issues", response_model=List[JiraIssue])
async def list_jira_issues(
    jql: Optional[str] = Query(None, description="Optional JQL search expression"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of issues to retrieve"),
):
    """
    Retrieve normalized Jira issues matching optional JQL or current project.
    Returns empty list if unconfigured or on communication error.
    """
    return await jira_service.get_issues(jql=jql or "", limit=limit)


@router.get("/issues/{issue_key}", response_model=JiraIssue)
async def get_jira_issue(issue_key: str):
    """
    Retrieve details for a specific Jira issue by key (e.g., 'PROJ-101').
    Returns 404 if issue does not exist or cannot be found.
    """
    issue = await jira_service.get_issue(issue_key)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jira issue '{issue_key}' not found or unreachable.",
        )
    return issue


@router.get("/evidence/{incident_id}", response_model=JiraEvidence)
async def get_incident_jira_evidence(incident_id: str):
    """
    Retrieve normalized Jira evidence deterministically correlated with an incident.
    Gracefully handles unconfigured or unreachable Jira without failing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, service, timestamp FROM incidents WHERE id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    return await jira_service.get_incident_jira_evidence(
        service=row["service"],
        incident_id=row["id"],
        title=row["title"],
        incident_timestamp=row["timestamp"],
    )
