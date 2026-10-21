"""
Jira Work Item and Incident Ticket Intelligence Service for IntelliIncident.
Provides normalized, read-only access to the Jira REST API (v2/v3) for
retrieving work items, tracking incident tickets, evaluating ticket context,
and feeding Jira work item evidence into Root Cause Analysis (RCA).
STRICTLY READ-ONLY: Never modifies Jira tickets, projects, or workflows.
STRICTLY SAFE: Never stores, logs, or returns authentication secrets.
"""

from typing import List, Optional, Dict, Any, Tuple
import datetime
import re
import httpx

from backend.app.core.config import settings
from backend.app.schemas.jira import (
    JiraStatusResponse,
    JiraIssue,
    JiraCorrelationMatch,
    JiraEvidence,
)

_UNSET = object()


def _extract_adf_text(adf_obj: Any) -> str:
    """Recursively extract plain text from Atlassian Document Format (ADF) or string."""
    if not adf_obj:
        return ""
    if isinstance(adf_obj, str):
        return adf_obj.strip()
    if not isinstance(adf_obj, dict):
        return ""

    text_parts: List[str] = []

    def _walk(node: Any):
        if isinstance(node, dict):
            if node.get("type") == "text" and "text" in node:
                text_parts.append(str(node["text"]))
            for child in node.get("content", []):
                _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf_obj)
    return " ".join(text_parts).strip()


class JiraService:
    """
    Client service for querying Jira Cloud and Server REST APIs.
    Normalizes Jira issues into structured evidence and deterministically
    correlates tickets with active operational incidents.
    """

    def __init__(
        self,
        base_url: Any = _UNSET,
        email: Any = _UNSET,
        api_token: Any = _UNSET,
        project_key: Any = _UNSET,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 4.0,
    ):
        resolved_url = settings.JIRA_BASE_URL if base_url is _UNSET else base_url
        self.base_url = (resolved_url or "").rstrip("/")
        self.email = settings.JIRA_EMAIL if email is _UNSET else email
        self._api_token = settings.JIRA_API_TOKEN if api_token is _UNSET else api_token
        resolved_proj = settings.JIRA_PROJECT_KEY if project_key is _UNSET else project_key
        self.project_key = resolved_proj.strip().upper() if resolved_proj and resolved_proj.strip() else None
        self._client = client
        self.timeout = timeout

    def _get_auth(self) -> Optional[httpx.Auth]:
        """Generate HTTP Basic Auth if email and token are configured."""
        if self.email and self._api_token:
            return httpx.BasicAuth(self.email.strip(), self._api_token.strip())
        return None

    def _get_headers(self) -> Dict[str, str]:
        """Headers for Jira REST requests (supports Bearer token if email is omitted)."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "IntelliIncident-JiraIntegration/1.0",
        }
        if self._api_token and not self.email:
            headers["Authorization"] = f"Bearer {self._api_token.strip()}"
        return headers

    def is_configured(self) -> bool:
        """Check if minimum required credentials and endpoints are present."""
        return bool(self.base_url and self._api_token)

    async def get_health(self) -> JiraStatusResponse:
        """
        Verify connectivity and authentication with Jira server.
        Never raises exceptions; always returns structured status response.
        """
        if not self.base_url:
            return JiraStatusResponse(
                configured=False,
                authenticated=False,
                reachable=False,
                base_url="",
                email=None,
                project_key=self.project_key,
                message="Jira base URL is not configured. Set JIRA_BASE_URL and JIRA_API_TOKEN.",
            )

        if not self._api_token:
            return JiraStatusResponse(
                configured=False,
                authenticated=False,
                reachable=False,
                base_url=self.base_url,
                email=self.email,
                project_key=self.project_key,
                message="Jira API token is not configured. Set JIRA_API_TOKEN.",
            )

        # Jira Cloud uses /rest/api/3/myself; fallback to /rest/api/2/myself
        endpoint = f"{self.base_url}/rest/api/3/myself"
        try:
            auth = self._get_auth()
            headers = self._get_headers()

            if self._client:
                resp = await self._client.get(endpoint, auth=auth, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(endpoint, auth=auth, headers=headers)

            if resp.status_code == 404:
                # Try v2 fallback
                v2_endpoint = f"{self.base_url}/rest/api/2/myself"
                if self._client:
                    resp = await self._client.get(v2_endpoint, auth=auth, headers=headers, timeout=self.timeout)
                else:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.get(v2_endpoint, auth=auth, headers=headers)

            if resp.status_code == 200:
                data = resp.json() if isinstance(resp.json(), dict) else {}
                display_name = data.get("displayName")
                email_addr = data.get("emailAddress") or self.email
                return JiraStatusResponse(
                    configured=True,
                    authenticated=True,
                    reachable=True,
                    base_url=self.base_url,
                    email=email_addr,
                    project_key=self.project_key,
                    user_display_name=display_name,
                    message="Jira connection verified and user authenticated successfully.",
                )
            elif resp.status_code in (401, 403):
                return JiraStatusResponse(
                    configured=True,
                    authenticated=False,
                    reachable=True,
                    base_url=self.base_url,
                    email=self.email,
                    project_key=self.project_key,
                    message=f"Jira authentication failed (HTTP {resp.status_code}). Check JIRA_EMAIL and JIRA_API_TOKEN.",
                )
            else:
                return JiraStatusResponse(
                    configured=True,
                    authenticated=False,
                    reachable=True,
                    base_url=self.base_url,
                    email=self.email,
                    project_key=self.project_key,
                    message=f"Jira returned unexpected status code {resp.status_code}.",
                )
        except httpx.TimeoutException:
            return JiraStatusResponse(
                configured=True,
                authenticated=False,
                reachable=False,
                base_url=self.base_url,
                email=self.email,
                project_key=self.project_key,
                message=f"Jira request timed out after {self.timeout}s.",
            )
        except httpx.ConnectError as e:
            return JiraStatusResponse(
                configured=True,
                authenticated=False,
                reachable=False,
                base_url=self.base_url,
                email=self.email,
                project_key=self.project_key,
                message=f"Cannot reach Jira server at {self.base_url}: {str(e)[:100]}",
            )
        except Exception as e:
            return JiraStatusResponse(
                configured=True,
                authenticated=False,
                reachable=False,
                base_url=self.base_url,
                email=self.email,
                project_key=self.project_key,
                message=f"Error checking Jira health: {str(e)[:100]}",
            )

    def _normalize_issue(self, raw_issue: Dict[str, Any]) -> JiraIssue:
        """Parse raw Jira JSON into normalized JiraIssue schema."""
        issue_id = str(raw_issue.get("id") or "")
        key = str(raw_issue.get("key") or "")
        fields = raw_issue.get("fields") or {}

        summary = fields.get("summary") or "Untitled Jira Issue"
        raw_desc = fields.get("description")
        description = _extract_adf_text(raw_desc) if raw_desc else None

        status_obj = fields.get("status") or {}
        status_name = status_obj.get("name") if isinstance(status_obj, dict) else str(status_obj)

        priority_obj = fields.get("priority") or {}
        priority_name = priority_obj.get("name") if isinstance(priority_obj, dict) else str(priority_obj)

        type_obj = fields.get("issuetype") or {}
        type_name = type_obj.get("name") if isinstance(type_obj, dict) else str(type_obj)

        proj_obj = fields.get("project") or {}
        proj_key = proj_obj.get("key") if isinstance(proj_obj, dict) else None
        proj_name = proj_obj.get("name") if isinstance(proj_obj, dict) else None

        labels = [str(l) for l in fields.get("labels", []) if l]
        raw_comps = fields.get("components", [])
        components = [c.get("name") for c in raw_comps if isinstance(c, dict) and c.get("name")]

        assignee_obj = fields.get("assignee")
        assignee_name = assignee_obj.get("displayName") if isinstance(assignee_obj, dict) else None

        reporter_obj = fields.get("reporter")
        reporter_name = reporter_obj.get("displayName") if isinstance(reporter_obj, dict) else None

        created = fields.get("created")
        updated = fields.get("updated")

        res_obj = fields.get("resolution")
        resolution = res_obj.get("name") if isinstance(res_obj, dict) else None

        url = f"{self.base_url}/browse/{key}" if self.base_url and key else None

        return JiraIssue(
            id=issue_id,
            key=key,
            summary=summary,
            description=description,
            issue_type=type_name or "Bug",
            status=status_name or "Open",
            priority=priority_name or "Medium",
            project_key=proj_key,
            project_name=proj_name,
            labels=labels,
            components=components,
            assignee=assignee_name,
            reporter=reporter_name,
            created=created,
            updated=updated,
            resolution=resolution,
            url=url,
        )

    async def get_issues(self, jql: str = "", limit: int = 20) -> List[JiraIssue]:
        """
        Execute JQL query against Jira Search API.
        Returns normalized list of Jira issues.
        """
        if not self.is_configured():
            return []

        endpoint = f"{self.base_url}/rest/api/3/search"
        params: Dict[str, Any] = {
            "maxResults": min(max(1, limit), 100),
            "fields": "id,key,summary,description,status,priority,issuetype,project,labels,components,assignee,reporter,created,updated,resolution",
        }
        if jql:
            params["jql"] = jql
        elif self.project_key:
            params["jql"] = f"project = '{self.project_key}' ORDER BY updated DESC"
        else:
            params["jql"] = "ORDER BY updated DESC"

        try:
            auth = self._get_auth()
            headers = self._get_headers()

            if self._client:
                resp = await self._client.get(endpoint, params=params, auth=auth, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(endpoint, params=params, auth=auth, headers=headers)

            if resp.status_code == 404:
                # Try v2 fallback
                v2_endpoint = f"{self.base_url}/rest/api/2/search"
                if self._client:
                    resp = await self._client.get(v2_endpoint, params=params, auth=auth, headers=headers, timeout=self.timeout)
                else:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.get(v2_endpoint, params=params, auth=auth, headers=headers)

            if resp.status_code != 200:
                return []

            body = resp.json() if isinstance(resp.json(), dict) else {}
            raw_issues = body.get("issues", [])
            return [self._normalize_issue(iss) for iss in raw_issues if isinstance(iss, dict)]
        except Exception:
            return []

    async def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """
        Retrieve single Jira issue by key or id.
        Returns normalized JiraIssue or None.
        """
        clean_key = issue_key.strip().upper()
        if not self.is_configured() or not clean_key:
            return None

        endpoint = f"{self.base_url}/rest/api/3/issue/{clean_key}"
        params = {
            "fields": "id,key,summary,description,status,priority,issuetype,project,labels,components,assignee,reporter,created,updated,resolution",
        }

        try:
            auth = self._get_auth()
            headers = self._get_headers()

            if self._client:
                resp = await self._client.get(endpoint, params=params, auth=auth, headers=headers, timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(endpoint, params=params, auth=auth, headers=headers)

            if resp.status_code == 404:
                v2_endpoint = f"{self.base_url}/rest/api/2/issue/{clean_key}"
                if self._client:
                    resp = await self._client.get(v2_endpoint, params=params, auth=auth, headers=headers, timeout=self.timeout)
                else:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.get(v2_endpoint, params=params, auth=auth, headers=headers)

            if resp.status_code == 200:
                data = resp.json() if isinstance(resp.json(), dict) else {}
                return self._normalize_issue(data)
            return None
        except Exception:
            return None

    def calculate_correlation(
        self,
        issue: JiraIssue,
        service: Optional[str] = None,
        incident_id: Optional[str] = None,
        title: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Tuple[float, List[str], str]:
        """
        Deterministically evaluate correlation between an incident and a Jira issue.
        Returns: (confidence_score, matched_by_signals, explanation)
        """
        score = 0.0
        matched_by: List[str] = []
        explanation_parts: List[str] = []

        issue_text = f"{issue.key} {issue.summary} {issue.description or ''}".lower()
        issue_labels = [l.lower() for l in issue.labels]
        issue_comps = [c.lower() for c in issue.components]

        # 1. Exact Incident ID match (strongest signal)
        if incident_id:
            clean_id = incident_id.strip().lower()
            if clean_id in issue_text or clean_id in issue_labels:
                score += 0.60
                matched_by.append("incident_id")
                explanation_parts.append(f"ticket explicitly cites incident ID '{incident_id}'")

        # 2. Service name match
        if service:
            clean_srv = service.strip().lower()
            if clean_srv in issue_text or clean_srv in issue_labels or clean_srv in issue_comps:
                score += 0.35
                matched_by.append("service_name")
                explanation_parts.append(f"ticket is scoped to affected service '{service}'")

        # 3. Environment match
        if environment:
            clean_env = environment.strip().lower()
            if clean_env in issue_text or clean_env in issue_labels:
                score += 0.15
                matched_by.append("environment")
                explanation_parts.append(f"environment matches '{environment}'")

        # 4. Domain & failure keyword match
        domain_keywords = [
            "timeout", "latency", "500", "502", "503", "504", "exception",
            "crash", "deadlock", "memory", "pool", "outage", "degradation",
            "connection", "failure", "unhandled"
        ]
        matched_kw = [kw for kw in domain_keywords if kw in issue_text]
        if matched_kw:
            score += min(0.20, len(matched_kw) * 0.08)
            matched_by.append("failure_keywords")
            explanation_parts.append(f"contains failure signals ({', '.join(matched_kw[:3])})")

        # 5. Incident title token match
        if title:
            tokens = [t.lower() for t in re.split(r"\W+", title) if len(t) >= 4 and t.lower() not in ("incident", "service", "error", "issue", "failure")]
            matched_tokens = [t for t in tokens if t in issue_text]
            if matched_tokens:
                score += min(0.15, len(matched_tokens) * 0.05)
                matched_by.append("title_keywords")

        final_score = min(round(score, 2), 1.0)
        explanation = "; ".join(explanation_parts) if explanation_parts else "No strong semantic correlation detected."
        return final_score, matched_by, explanation

    async def get_incident_jira_evidence(
        self,
        service: Optional[str] = None,
        incident_id: Optional[str] = None,
        title: Optional[str] = None,
        incident_timestamp: Optional[str] = None,
        environment: Optional[str] = None,
        explicit_issue_key: Optional[str] = None,
    ) -> JiraEvidence:
        """
        Produce first-class, normalized Jira evidence for an incident.
        Never throws; gracefully returns unconfigured/unavailable/no-match states.
        """
        health = await self.get_health()
        if not health.configured:
            return JiraEvidence(
                status="NOT_CONFIGURED",
                base_url=self.base_url,
                project_key=self.project_key,
                total_issues_found=0,
                matched_issues=[],
                primary_issue=None,
                correlation=None,
                correlation_strength="NONE",
                summary="Jira integration is not configured. Telemetry proceeding without Jira work item context.",
            )

        if not health.reachable or not health.authenticated:
            status_code = "AUTH_ERROR" if not health.authenticated and health.reachable else "UNAVAILABLE"
            return JiraEvidence(
                status=status_code,
                base_url=self.base_url,
                project_key=self.project_key,
                total_issues_found=0,
                matched_issues=[],
                primary_issue=None,
                correlation=None,
                correlation_strength="NONE",
                summary=f"Jira integration is {status_code.lower()}: {health.message}",
            )

        candidate_issues: List[JiraIssue] = []

        # If explicit issue key provided, fetch directly
        if explicit_issue_key:
            single_iss = await self.get_issue(explicit_issue_key)
            if single_iss:
                candidate_issues.append(single_iss)

        # Otherwise, search Jira for recent issues scoped to project or service
        if not candidate_issues:
            jql_parts: List[str] = []
            if self.project_key:
                jql_parts.append(f"project = '{self.project_key}'")

            # Target matching by service or incident ID
            if service:
                jql_parts.append(f'(text ~ "{service}" OR labels = "{service}")')

            jql = " AND ".join(jql_parts) + " ORDER BY updated DESC" if jql_parts else "ORDER BY updated DESC"
            candidate_issues = await self.get_issues(jql=jql, limit=15)

            # If service-scoped search returned 0 issues, fallback to project-wide recent issues
            if not candidate_issues and self.project_key:
                candidate_issues = await self.get_issues(jql=f"project = '{self.project_key}' ORDER BY updated DESC", limit=10)

        if not candidate_issues:
            return JiraEvidence(
                status="NO_ISSUES_FOUND",
                base_url=self.base_url,
                project_key=self.project_key,
                total_issues_found=0,
                matched_issues=[],
                primary_issue=None,
                correlation=None,
                correlation_strength="NONE",
                summary="Connected to Jira. No active work items or incident tickets found matching service criteria.",
            )

        # Score and rank candidates
        scored_candidates: List[Tuple[float, JiraIssue, List[str], str]] = []
        for issue in candidate_issues:
            score, matched_by, explanation = self.calculate_correlation(
                issue=issue,
                service=service,
                incident_id=incident_id,
                title=title,
                environment=environment,
            )
            if score >= 0.20:
                scored_candidates.append((score, issue, matched_by, explanation))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        if not scored_candidates:
            return JiraEvidence(
                status="NO_ISSUES_FOUND",
                base_url=self.base_url,
                project_key=self.project_key,
                total_issues_found=len(candidate_issues),
                matched_issues=[],
                primary_issue=None,
                correlation=None,
                correlation_strength="NONE",
                summary=f"Inspected {len(candidate_issues)} Jira issues; none exhibited sufficient correlation to this incident.",
            )

        top_score, top_issue, top_matches, top_explanation = scored_candidates[0]
        correlation_strength = "HIGH" if top_score >= 0.50 else "MEDIUM" if top_score >= 0.30 else "LOW"

        correlation_meta = JiraCorrelationMatch(
            matched_by=top_matches,
            confidence_score=top_score,
            explanation=top_explanation,
        )

        matched_list = [item[1] for item in scored_candidates[:5]]

        summary = (
            f"Correlated Jira issue {top_issue.key} ('{top_issue.summary}') with {correlation_strength.lower()} "
            f"confidence ({int(top_score * 100)}% match score): {top_explanation}."
        )

        return JiraEvidence(
            status="CONNECTED",
            base_url=self.base_url,
            project_key=self.project_key,
            total_issues_found=len(candidate_issues),
            matched_issues=matched_list,
            primary_issue=top_issue,
            correlation=correlation_meta,
            correlation_strength=correlation_strength,
            summary=summary,
        )
