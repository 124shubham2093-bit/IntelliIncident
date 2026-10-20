"""
Sentry Runtime Error Evidence Schemas for IntelliIncident.
Defines normalized Pydantic models for Sentry projects, issues, events,
exceptions, stack frames, and evidence correlation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SentryRateLimit(BaseModel):
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_at: Optional[int] = None
    retry_after: Optional[int] = None


class SentryStatusResponse(BaseModel):
    configured: bool
    authenticated: bool
    reachable: bool
    org_slug: Optional[str] = None
    project_slug: Optional[str] = None
    base_url: str
    rate_limit: Optional[SentryRateLimit] = None
    message: Optional[str] = None
    sdk_initialized: Optional[bool] = None


class SentryProject(BaseModel):
    id: str
    slug: str
    name: str
    platform: Optional[str] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None
    date_created: Optional[str] = None


class SentryStackFrame(BaseModel):
    filename: Optional[str] = None
    abs_path: Optional[str] = None
    module: Optional[str] = None
    function: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None
    in_app: Optional[bool] = None
    context_line: Optional[str] = None
    pre_context: Optional[List[str]] = Field(default_factory=list)
    post_context: Optional[List[str]] = Field(default_factory=list)


class SentryException(BaseModel):
    type: str
    value: Optional[str] = None
    module: Optional[str] = None
    frames: List[SentryStackFrame] = Field(default_factory=list)


class SentryTag(BaseModel):
    key: str
    value: str


class SentryEvent(BaseModel):
    id: str
    event_id: str
    title: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    platform: Optional[str] = None
    environment: Optional[str] = None
    release: Optional[str] = None
    culprit: Optional[str] = None
    exceptions: List[SentryException] = Field(default_factory=list)
    tags: List[SentryTag] = Field(default_factory=list)
    permalink: Optional[str] = None


class SentryIssue(BaseModel):
    id: str
    short_id: Optional[str] = None
    title: str
    culprit: Optional[str] = None
    type: Optional[str] = None
    level: Optional[str] = None
    count: int = 0
    user_count: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    permalink: Optional[str] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    latest_event: Optional[SentryEvent] = None


class SentryEvidence(BaseModel):
    status: str  # "CONNECTED", "NO_ISSUES_FOUND", "NOT_CONFIGURED", "UNAVAILABLE", "AUTH_ERROR", "RATE_LIMITED"
    org_slug: Optional[str] = None
    project_slug: Optional[str] = None
    issue_count: int = 0
    issues: List[SentryIssue] = Field(default_factory=list)
    latest_issue: Optional[SentryIssue] = None
    latest_event: Optional[SentryEvent] = None
    matched_exception_type: Optional[str] = None
    matched_exception_value: Optional[str] = None
    matched_stack_trace_frames: List[SentryStackFrame] = Field(default_factory=list)
    correlated_release: Optional[str] = None
    correlated_environment: Optional[str] = None
    message: str
