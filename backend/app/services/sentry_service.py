"""
Sentry Runtime Error Intelligence Service for IntelliIncident.
Provides normalized, read-only access to the Sentry REST API (v0) for
retrieving projects, issues, events, runtime exceptions, and stack frames
for evidence correlation and Root Cause Analysis.
"""

from typing import List, Optional, Dict, Any, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.schemas.sentry import (
    SentryRateLimit,
    SentryStatusResponse,
    SentryProject,
    SentryStackFrame,
    SentryException,
    SentryTag,
    SentryEvent,
    SentryIssue,
    SentryEvidence,
)


class SentryError(Exception):
    """Base exception for Sentry API errors."""
    pass


class SentryConfigError(SentryError):
    """Raised when Sentry organization or project slug configuration is missing."""
    pass


class SentryAuthError(SentryError):
    """Raised when Sentry authentication fails (HTTP 401)."""
    pass


class SentryPermissionError(SentryError):
    """Raised when Sentry permissions are insufficient or access is forbidden (HTTP 403)."""
    pass


class SentryRateLimitError(SentryError):
    """Raised when Sentry API rate limit is exceeded (HTTP 429)."""
    pass


class SentryNotFoundError(SentryError):
    """Raised when Sentry organization, project, issue, or event is not found (HTTP 404)."""
    pass


class SentryUnavailableError(SentryError):
    """Raised when Sentry API is unreachable, times out, or returns a 5xx error."""
    pass


_UNSET = object()


class SentryService:
    """
    Client service for interacting with the official Sentry REST API (v0).
    Normalizes remote telemetry into typed Pydantic models for safe consumption
    by IntelliIncident's EvidenceCorrelator and RootCauseEngine.
    STRICTLY READ-ONLY: Never modifies, acknowledges, resolves, or creates Sentry data.
    """

    def __init__(
        self,
        auth_token: Any = _UNSET,
        org_slug: Any = _UNSET,
        project_slug: Any = _UNSET,
        base_url: Any = _UNSET,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 4.0,
    ):
        self.auth_token = settings.SENTRY_AUTH_TOKEN if auth_token is _UNSET else auth_token
        self.org_slug = settings.SENTRY_ORG_SLUG if org_slug is _UNSET else org_slug
        self.project_slug = settings.SENTRY_PROJECT_SLUG if project_slug is _UNSET else project_slug
        resolved_base = settings.SENTRY_BASE_URL if base_url is _UNSET else (base_url or "https://sentry.io")
        self.base_url = (resolved_base or "https://sentry.io").rstrip("/")
        self._client = client
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "IntelliIncident-SentryIntegration/1.0",
        }
        if self.auth_token and self.auth_token.strip():
            headers["Authorization"] = f"Bearer {self.auth_token.strip()}"
        return headers

    @staticmethod
    def _parse_rate_limit(headers: httpx.Headers) -> Optional[SentryRateLimit]:
        remaining = headers.get("x-sentry-rate-limit-remaining")
        reset_at = headers.get("x-sentry-rate-limit-reset")
        retry_after = headers.get("retry-after")
        if remaining is not None or retry_after is not None or reset_at is not None:
            try:
                return SentryRateLimit(
                    remaining=int(remaining) if remaining is not None else None,
                    reset_at=int(reset_at) if reset_at is not None else None,
                    retry_after=int(retry_after) if retry_after is not None else None,
                )
            except (ValueError, TypeError):
                return None
        return None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[httpx.Response, Any]:
        """
        Execute an HTTP request against the Sentry API v0.
        Translates HTTP status codes into typed application exceptions.
        Never logs or exposes the auth token.
        """
        url = f"{self.base_url}/api/0{endpoint}"
        headers = self._get_headers()

        try:
            if self._client:
                resp = await self._client.request(
                    method, url, headers=headers, params=params, timeout=self.timeout
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.request(
                        method, url, headers=headers, params=params
                    )
        except (httpx.ConnectError, httpx.NetworkError) as e:
            raise SentryUnavailableError(f"Unable to connect to Sentry API at {self.base_url}: {str(e)}")
        except httpx.TimeoutException as e:
            raise SentryUnavailableError(f"Sentry API request timed out after {self.timeout}s: {str(e)}")
        except httpx.RequestError as e:
            raise SentryUnavailableError(f"Sentry API network error: {str(e)}")

        if resp.status_code == 401:
            raise SentryAuthError("Sentry authentication failed. Auth token may be invalid, expired, or missing.")
        elif resp.status_code == 403:
            raise SentryPermissionError("Sentry access forbidden. Token lacks required organization/project permissions.")
        elif resp.status_code == 404:
            raise SentryNotFoundError(f"Sentry resource not found at endpoint: {endpoint}")
        elif resp.status_code == 429:
            rl = self._parse_rate_limit(resp.headers)
            retry_sec = rl.retry_after if rl and rl.retry_after is not None else 60
            raise SentryRateLimitError(f"Sentry API rate limit exceeded. Retry after {retry_sec}s.")
        elif resp.status_code >= 500:
            raise SentryUnavailableError(f"Sentry remote server error: HTTP {resp.status_code}")
        elif resp.status_code >= 400:
            raise SentryError(f"Sentry API error: HTTP {resp.status_code}")

        try:
            data = resp.json()
        except Exception as e:
            raise SentryError(f"Malformed JSON in Sentry response: {str(e)}")

        return resp, data

    async def get_status(self) -> SentryStatusResponse:
        """
        Check Sentry configuration, authentication, and reachability.
        Safe method that never raises exceptions and never exposes SENTRY_AUTH_TOKEN.
        """
        is_configured = bool(self.org_slug and self.project_slug)
        has_token = bool(self.auth_token and self.auth_token.strip())

        try:
            from backend.app.core.sentry import is_sentry_sdk_active
            sdk_active = is_sentry_sdk_active()
        except Exception:
            sdk_active = False

        if not is_configured:
            return SentryStatusResponse(
                configured=False,
                authenticated=has_token,
                reachable=False,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message="Sentry organization slug or project slug is not configured.",
                sdk_initialized=sdk_active,
            )

        if not has_token:
            return SentryStatusResponse(
                configured=True,
                authenticated=False,
                reachable=False,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message="Sentry organization and project configured, but auth token is missing.",
                sdk_initialized=sdk_active,
            )

        try:
            endpoint = f"/projects/{self.org_slug}/{self.project_slug}/"
            resp, _ = await self._request("GET", endpoint)
            rate_limit = self._parse_rate_limit(resp.headers)
            return SentryStatusResponse(
                configured=True,
                authenticated=True,
                reachable=True,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                rate_limit=rate_limit,
                message="Sentry integration operational and project verified.",
                sdk_initialized=sdk_active,
            )
        except SentryAuthError:
            return SentryStatusResponse(
                configured=True,
                authenticated=False,
                reachable=True,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message="Sentry authentication failed. Auth token is invalid or expired.",
                sdk_initialized=sdk_active,
            )
        except SentryPermissionError:
            return SentryStatusResponse(
                configured=True,
                authenticated=True,
                reachable=True,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message="Sentry token lacks permission to view the configured organization or project.",
                sdk_initialized=sdk_active,
            )
        except SentryNotFoundError:
            return SentryStatusResponse(
                configured=True,
                authenticated=True,
                reachable=True,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message=f"Sentry project '{self.project_slug}' not found under organization '{self.org_slug}'.",
                sdk_initialized=sdk_active,
            )
        except SentryRateLimitError as e:
            return SentryStatusResponse(
                configured=True,
                authenticated=True,
                reachable=True,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message=str(e),
                sdk_initialized=sdk_active,
            )
        except SentryUnavailableError as e:
            return SentryStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=False,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message=f"Sentry API unreachable: {str(e)}",
                sdk_initialized=sdk_active,
            )
        except Exception as e:
            return SentryStatusResponse(
                configured=True,
                authenticated=has_token,
                reachable=False,
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                base_url=self.base_url,
                message=f"Sentry check failed: {str(e)}",
                sdk_initialized=sdk_active,
            )

    async def get_project(self) -> SentryProject:
        """
        Retrieve Sentry project metadata.
        """
        if not self.org_slug or not self.project_slug:
            raise SentryConfigError("Sentry organization slug or project slug is not configured.")

        endpoint = f"/projects/{self.org_slug}/{self.project_slug}/"
        _, data = await self._request("GET", endpoint)

        return SentryProject(
            id=str(data.get("id", "")),
            slug=str(data.get("slug", self.project_slug)),
            name=str(data.get("name", self.project_slug)),
            platform=data.get("platform"),
            status=data.get("status"),
            is_public=data.get("isPublic"),
            date_created=data.get("dateCreated"),
        )

    def _normalize_issue(self, raw: Dict[str, Any]) -> SentryIssue:
        metadata = raw.get("metadata") or {}
        return SentryIssue(
            id=str(raw.get("id", "")),
            short_id=raw.get("shortId"),
            title=str(raw.get("title") or raw.get("culprit") or "Unhandled Sentry Exception"),
            culprit=raw.get("culprit"),
            type=raw.get("type"),
            level=raw.get("level"),
            count=int(raw.get("count") or 1),
            user_count=int(raw.get("userCount") or 0),
            first_seen=raw.get("firstSeen"),
            last_seen=raw.get("lastSeen"),
            permalink=raw.get("permalink"),
            status=raw.get("status"),
            metadata=metadata,
        )

    def _normalize_event(self, raw: Dict[str, Any]) -> SentryEvent:
        event_id = str(raw.get("eventID") or raw.get("id") or "")
        tags_raw = raw.get("tags") or []
        tags: List[SentryTag] = []
        if isinstance(tags_raw, list):
            for t in tags_raw:
                if isinstance(t, dict) and "key" in t and "value" in t:
                    tags.append(SentryTag(key=str(t["key"]), value=str(t["value"])))

        # Extract release
        release = None
        rel_data = raw.get("release")
        if isinstance(rel_data, dict):
            release = rel_data.get("version") or rel_data.get("shortVersion")
        elif isinstance(rel_data, str):
            release = rel_data

        # Extract environment
        env = raw.get("environment")
        if not env:
            for t in tags:
                if t.key == "environment":
                    env = t.value
                    break

        # Extract exceptions and stack traces from Sentry entries
        exceptions: List[SentryException] = []
        entries = raw.get("entries") or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get("type")
            if entry_type == "exception":
                entry_data = entry.get("data") or {}
                values = entry_data.get("values") or []
                for val in values:
                    if not isinstance(val, dict):
                        continue
                    exc_type = val.get("type") or "Exception"
                    exc_val = val.get("value")
                    exc_mod = val.get("module")

                    frames: List[SentryStackFrame] = []
                    st = val.get("stacktrace") or {}
                    st_frames = st.get("frames") or []
                    for f in st_frames:
                        if not isinstance(f, dict):
                            continue
                        frames.append(
                            SentryStackFrame(
                                filename=f.get("filename"),
                                abs_path=f.get("absPath"),
                                module=f.get("module"),
                                function=f.get("function"),
                                lineno=f.get("lineNo") or f.get("lineno"),
                                colno=f.get("colNo") or f.get("colno"),
                                in_app=f.get("inApp"),
                                context_line=f.get("context_line") or f.get("context"),
                                pre_context=f.get("pre_context") or [],
                                post_context=f.get("post_context") or [],
                            )
                        )

                    exceptions.append(
                        SentryException(
                            type=exc_type,
                            value=exc_val,
                            module=exc_mod,
                            frames=frames,
                        )
                    )

        # Fallback if no entries found but top-level exception/metadata exists
        if not exceptions and raw.get("metadata"):
            meta = raw["metadata"]
            if meta.get("type"):
                exceptions.append(
                    SentryException(
                        type=meta["type"],
                        value=meta.get("value"),
                        module=meta.get("module"),
                        frames=[],
                    )
                )

        return SentryEvent(
            id=str(raw.get("id", event_id)),
            event_id=event_id,
            title=raw.get("title") or raw.get("message"),
            message=raw.get("message"),
            timestamp=raw.get("dateCreated") or raw.get("timestamp"),
            platform=raw.get("platform"),
            environment=env,
            release=release,
            culprit=raw.get("culprit"),
            exceptions=exceptions,
            tags=tags,
            permalink=raw.get("permalink"),
        )

    async def get_issues(
        self,
        query: Optional[str] = "is:unresolved",
        limit: int = 10,
    ) -> List[SentryIssue]:
        """
        List unresolved or filtered issues for the configured project.
        """
        if not self.org_slug or not self.project_slug:
            raise SentryConfigError("Sentry organization slug or project slug is not configured.")

        params: Dict[str, Any] = {"limit": min(limit, 50)}
        if query:
            params["query"] = query

        endpoint = f"/projects/{self.org_slug}/{self.project_slug}/issues/"
        _, data = await self._request("GET", endpoint, params=params)

        if not isinstance(data, list):
            return []

        return [self._normalize_issue(item) for item in data if isinstance(item, dict)]

    async def get_issue(self, issue_id: str) -> SentryIssue:
        """
        Get details of a single Sentry issue by issue ID.
        """
        if not issue_id:
            raise SentryNotFoundError("Sentry issue ID must be provided.")

        endpoint = f"/issues/{issue_id}/"
        _, data = await self._request("GET", endpoint)
        return self._normalize_issue(data)

    async def get_issue_events(
        self,
        issue_id: str,
        limit: int = 5,
    ) -> List[SentryEvent]:
        """
        Get events associated with a specific issue.
        """
        if not issue_id:
            return []

        endpoint = f"/issues/{issue_id}/events/"
        params = {"limit": min(limit, 20)}
        _, data = await self._request("GET", endpoint, params=params)

        if not isinstance(data, list):
            return []

        return [self._normalize_event(item) for item in data if isinstance(item, dict)]

    async def get_latest_event(self, issue_id: str) -> Optional[SentryEvent]:
        """
        Get the latest event for an issue.
        """
        if not issue_id:
            return None

        endpoint = f"/issues/{issue_id}/events/latest/"
        try:
            _, data = await self._request("GET", endpoint)
            return self._normalize_event(data)
        except SentryNotFoundError:
            events = await self.get_issue_events(issue_id, limit=1)
            return events[0] if events else None

    async def get_runtime_evidence(
        self,
        service: Optional[str] = None,
        environment: Optional[str] = None,
        release: Optional[str] = None,
        limit: int = 5,
    ) -> SentryEvidence:
        """
        Retrieve and normalize runtime error evidence from Sentry for incident RCA.
        Never crashes or raises remote errors; returns structured SentryEvidence safely.
        """
        if not self.org_slug or not self.project_slug or not self.auth_token:
            return SentryEvidence(
                status="NOT_CONFIGURED",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                issue_count=0,
                message="Sentry integration is not configured or auth token is missing.",
            )

        try:
            query_parts = ["is:unresolved"]
            if environment and environment != "ALL":
                query_parts.append(f"environment:{environment}")
            query_str = " ".join(query_parts)

            issues = await self.get_issues(query=query_str, limit=limit)
            if not issues:
                return SentryEvidence(
                    status="NO_ISSUES_FOUND",
                    org_slug=self.org_slug,
                    project_slug=self.project_slug,
                    issue_count=0,
                    message="Sentry project accessible; no unresolved runtime error issues found.",
                )

            latest_issue = issues[0]
            latest_event = None
            try:
                latest_event = await self.get_latest_event(latest_issue.id)
            except Exception:
                pass

            matched_exc_type = None
            matched_exc_val = None
            matched_frames: List[SentryStackFrame] = []

            if latest_event and latest_event.exceptions:
                top_exc = latest_event.exceptions[0]
                matched_exc_type = top_exc.type
                matched_exc_val = top_exc.value
                matched_frames = top_exc.frames
            elif latest_issue.metadata:
                matched_exc_type = latest_issue.metadata.get("type")
                matched_exc_val = latest_issue.metadata.get("value")

            corr_release = latest_event.release if latest_event else None
            corr_env = latest_event.environment if latest_event else environment

            return SentryEvidence(
                status="CONNECTED",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                issue_count=len(issues),
                issues=issues,
                latest_issue=latest_issue,
                latest_event=latest_event,
                matched_exception_type=matched_exc_type,
                matched_exception_value=matched_exc_val,
                matched_stack_trace_frames=matched_frames,
                correlated_release=corr_release,
                correlated_environment=corr_env,
                message=f"Retrieved {len(issues)} unresolved Sentry error issue(s). Latest: {latest_issue.title}",
            )

        except SentryAuthError as e:
            return SentryEvidence(
                status="AUTH_ERROR",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                message=f"Sentry authentication failure: {str(e)}",
            )
        except SentryPermissionError as e:
            return SentryEvidence(
                status="PERMISSION_ERROR",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                message=f"Sentry permission denied: {str(e)}",
            )
        except SentryRateLimitError as e:
            return SentryEvidence(
                status="RATE_LIMITED",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                message=f"Sentry rate limit reached: {str(e)}",
            )
        except SentryNotFoundError as e:
            return SentryEvidence(
                status="NOT_FOUND",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                message=f"Sentry project or resource not found: {str(e)}",
            )
        except SentryUnavailableError as e:
            return SentryEvidence(
                status="UNAVAILABLE",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                message=f"Sentry service unavailable: {str(e)}",
            )
        except Exception as e:
            return SentryEvidence(
                status="ERROR",
                org_slug=self.org_slug,
                project_slug=self.project_slug,
                message=f"Failed to retrieve Sentry evidence: {str(e)}",
            )
