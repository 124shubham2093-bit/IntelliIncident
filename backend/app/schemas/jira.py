"""
Jira Work Item and Incident Ticket Evidence Schemas for IntelliIncident.
Defines normalized Pydantic models for Jira connectivity status, issue summaries,
issue details, correlation metadata, and RCA evidence integration.
STRICTLY SAFE: Never stores or exposes API tokens.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class JiraStatusResponse(BaseModel):
    """Normalized health, connectivity, and authentication status for Jira."""
    configured: bool
    authenticated: bool
    reachable: bool
    base_url: str
    email: Optional[str] = None
    project_key: Optional[str] = None
    user_display_name: Optional[str] = None
    server_title: Optional[str] = None
    version: Optional[str] = None
    message: str


class JiraIssue(BaseModel):
    """Normalized representation of a Jira issue/ticket."""
    id: str
    key: str  # e.g., "PROJ-101"
    summary: str
    description: Optional[str] = None
    issue_type: str = "Bug"
    status: str = "Open"
    priority: str = "Medium"
    project_key: Optional[str] = None
    project_name: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    resolution: Optional[str] = None
    url: Optional[str] = None


class JiraCorrelationMatch(BaseModel):
    """Deterministic explanation and score for an incident-to-issue match."""
    matched_by: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    explanation: str = ""


class JiraEvidence(BaseModel):
    """First-class evidence structure fed into EvidenceCorrelator and RootCauseEngine."""
    status: str  # "CONNECTED", "NO_ISSUES_FOUND", "NOT_CONFIGURED", "UNAVAILABLE", "AUTH_ERROR", "ERROR"
    base_url: str
    project_key: Optional[str] = None
    total_issues_found: int = 0
    matched_issues: List[JiraIssue] = Field(default_factory=list)
    primary_issue: Optional[JiraIssue] = None
    correlation: Optional[JiraCorrelationMatch] = None
    correlation_strength: Literal["NONE", "LOW", "MEDIUM", "HIGH"] = "NONE"
    summary: str
