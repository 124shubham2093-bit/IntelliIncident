"""
Tests for Sentry Runtime Error Evidence Correlation with RCA Engine.
Validates:
1. EvidenceCorrelator CODE_ERROR enrichment with Sentry issues & exception types.
2. EvidenceCorrelator CODE_ERROR cross-correlation with GitHub commit files.
3. EvidenceCorrelator DEPLOYMENT enrichment when Sentry release matches commit SHA.
4. EvidenceCorrelator DATABASE enrichment when Sentry has DB-related exceptions.
5. Baseline correlation behavior without Sentry evidence (or when empty/unconfigured).
6. RootCauseEngine forwarding of sentry_evidence.
7. IncidentService graceful handling of Sentry errors (shielding).
8. Strict score preservation (no arbitrary score increments).
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.app.rca.evidence_correlator import EvidenceCorrelator
from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.services.incident_service import IncidentService
from backend.app.schemas.sentry import (
    SentryEvidence,
    SentryIssue,
    SentryEvent,
    SentryException,
    SentryStackFrame,
)
from backend.app.services.sentry_service import (
    SentryAuthError,
    SentryNotFoundError,
    SentryUnavailableError,
)

SAMPLE_INCIDENT = {
    "id": "INC-TEST-1",
    "service": "order-service",
    "title": "Order Processing Failure",
    "severity": "CRITICAL",
}

SAMPLE_METRICS = {
    "service": "order-service",
    "affectedUsers": 500,
    "errorRate": 25.0,
    "latencyP99": 350.0,
    "latencyP50": 80.0,
    "requestVolume": 2000,
    "deploymentRecencyMinutes": 30,
    "cpuUtilization": 45.0,
    "memoryUtilization": 50.0,
}

SAMPLE_LOGS = [
    {
        "id": "LOG-1",
        "message": "NullPointerException encountered in OrderService",
        "stack_trace": "java.lang.NullPointerException at services.OrderService.process(OrderService.java:45)",
    }
]

SAMPLE_DEPLOYMENTS = [
    {
        "id": "DEP-1",
        "service": "order-service",
        "commit_hash": "a1b2c3d",
        "deployed_at": "2026-09-26T12:00:00Z",
        "environment": "production",
        "status": "SUCCESS",
    }
]

SAMPLE_GITHUB_COMMIT = {
    "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
    "short_sha": "a1b2c3d",
    "message": "fix: update order processing",
    "author": {"name": "Jane Dev", "email": "jane@example.com"},
    "files": [
        {"filename": "services/OrderService.java", "status": "modified", "changes": 10},
    ],
}

SAMPLE_SENTRY_EVIDENCE = {
    "status": "CONNECTED",
    "issue_count": 2,
    "unresolved_issue_count": 2,
    "matched_exception_type": "NullPointerException",
    "matched_exception_value": "Order object reference was null",
    "correlated_release": "a1b2c3d",
    "correlated_environment": "production",
    "matched_stack_trace_frames": [
        {
            "filename": "services/OrderService.java",
            "function": "process",
            "module": "services.OrderService",
            "lineno": 45,
            "in_app": True,
        }
    ],
    "message": "Sentry retrieved 2 unresolved issue(s).",
}


def test_evidence_correlator_code_error_sentry():
    """Verify CODE_ERROR includes Sentry issue count, exception type, and preserves base score."""
    res_without = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, []
    )
    res_with = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT,
        SAMPLE_METRICS,
        SAMPLE_LOGS,
        SAMPLE_DEPLOYMENTS,
        [],
        sentry_evidence=SAMPLE_SENTRY_EVIDENCE,
    )

    code_ev = res_with["CODE_ERROR"]["evidence"]
    assert any("Sentry reports" in ev and "NullPointerException" in ev for ev in code_ev)
    # Score must be strictly preserved (no unexplained bumps)
    assert res_with["CODE_ERROR"]["score"] == res_without["CODE_ERROR"]["score"]


def test_evidence_correlator_cross_source_github_sentry():
    """Verify cross-source correlation when Sentry stack frame matches GitHub changed file."""
    res = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT,
        SAMPLE_METRICS,
        SAMPLE_LOGS,
        SAMPLE_DEPLOYMENTS,
        [],
        github_commits=[SAMPLE_GITHUB_COMMIT],
        sentry_evidence=SAMPLE_SENTRY_EVIDENCE,
    )

    code_ev = res["CODE_ERROR"]["evidence"]
    cross_source_ev = [ev for ev in code_ev if "Cross-source correlation" in ev]
    assert len(cross_source_ev) == 1
    assert "services/OrderService.java" in cross_source_ev[0]
    assert "Sentry stack trace frame" in cross_source_ev[0]
    assert "deployment commit a1b2c3d" in cross_source_ev[0]


def test_evidence_correlator_deployment_sentry_release():
    """Verify DEPLOYMENT evidence notes Sentry release correlation."""
    res = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT,
        SAMPLE_METRICS,
        SAMPLE_LOGS,
        SAMPLE_DEPLOYMENTS,
        [],
        sentry_evidence=SAMPLE_SENTRY_EVIDENCE,
    )

    dep_ev = res["DEPLOYMENT"]["evidence"]
    assert any("Sentry error events tagged with release 'a1b2c3d'" in ev for ev in dep_ev)


def test_evidence_correlator_database_sentry_exception():
    """Verify DATABASE evidence notes Sentry database connection/pool exceptions."""
    sentry_db_evidence = {
        "status": "CONNECTED",
        "issue_count": 1,
        "matched_exception_type": "DatabaseTimeoutException",
        "matched_exception_value": "Connection pool timeout after 30s",
        "matched_stack_trace_frames": [],
        "message": "Sentry found 1 DB issue.",
    }

    res = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT,
        SAMPLE_METRICS,
        SAMPLE_LOGS,
        SAMPLE_DEPLOYMENTS,
        [],
        sentry_evidence=sentry_db_evidence,
    )

    db_ev = res["DATABASE"]["evidence"]
    assert any("Sentry captured runtime database exception" in ev for ev in db_ev)
    assert any("DatabaseTimeoutException" in ev for ev in db_ev)


def test_evidence_correlator_without_sentry():
    """Verify omitting sentry_evidence leaves baseline correlation intact."""
    res_none = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [], sentry_evidence=None
    )
    res_empty = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [], sentry_evidence={}
    )
    assert res_none == res_empty


def test_root_cause_engine_passes_sentry():
    """Verify RootCauseEngine forwards sentry_evidence into candidates."""
    engine = RootCauseEngine()
    candidates = engine.analyze(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        github_commits=[SAMPLE_GITHUB_COMMIT],
        sentry_evidence=SAMPLE_SENTRY_EVIDENCE,
    )

    code_candidate = next(c for c in candidates if c["category"] == "CODE_ERROR")
    assert any("Sentry reports" in ev for ev in code_candidate["evidence"])
    assert any("Cross-source correlation" in ev for ev in code_candidate["evidence"])


def test_incident_api_sentry_error_shielding(client):
    """Verify GET /api/incidents/{id} shields Sentry API failures gracefully."""
    list_res = client.get("/api/incidents")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) > 0
    first_id = incidents[0]["id"]

    mock_unavail = SentryEvidence(
        status="UNAVAILABLE",
        message="Sentry API unreachable: 503 Service Unavailable",
    )

    with patch("backend.app.services.incident_service.SentryService.get_runtime_evidence", new_callable=AsyncMock) as mock_sentry:
        mock_sentry.return_value = mock_unavail
        resp = client.get(f"/api/incidents/{first_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == first_id
    assert "rootCauseCandidates" in data
    assert "sentryEvidence" in data
    assert data["sentryEvidence"]["status"] == "UNAVAILABLE"
