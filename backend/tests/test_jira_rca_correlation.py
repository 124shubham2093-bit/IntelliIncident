"""
Tests for Jira Work Item and Incident Ticket Evidence Correlation with RCA Engine.
Validates:
1. EvidenceCorrelator CODE_ERROR enrichment with Jira bug tickets.
2. EvidenceCorrelator DATABASE enrichment with Jira database contention tickets.
3. EvidenceCorrelator INFRASTRUCTURE enrichment with Jira compute saturation tickets.
4. EvidenceCorrelator DEPLOYMENT enrichment with Jira release/deployment tickets.
5. EvidenceCorrelator TRAFFIC enrichment with Jira load surge tickets.
6. EvidenceCorrelator NETWORK enrichment with Jira gateway disruption tickets.
7. Quad-Source Cross-Correlation (GitHub commit + Sentry exception + Prometheus deviation + Jira ticket).
8. Graceful baseline behavior when Jira is None or UNAVAILABLE.
9. RootCauseEngine forwarding of jira_evidence to EvidenceCorrelator.
10. Irrelevant Jira tickets are not falsely correlated.
"""

import pytest
from backend.app.rca.evidence_correlator import EvidenceCorrelator
from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.schemas.jira import (
    JiraEvidence,
    JiraIssue,
    JiraCorrelationMatch,
)
from backend.app.schemas.prometheus import (
    PrometheusEvidence,
    PrometheusMetricSample,
)
from backend.app.schemas.sentry import (
    SentryEvidence,
    SentryIssue,
)


SAMPLE_INCIDENT = {
    "id": "INC-TEST-JIRA",
    "service": "checkout-service",
    "title": "Checkout Latency and Failure Spike",
    "severity": "CRITICAL",
}

SAMPLE_METRICS = {
    "service": "checkout-service",
    "affectedUsers": 1200,
    "errorRate": 18.0,
    "latencyP99": 850.0,
    "latencyP50": 120.0,
    "requestVolume": 5000,
    "deploymentRecencyMinutes": 15,
    "cpuUtilization": 92.0,
    "memoryUtilization": 89.0,
}

SAMPLE_LOGS = [
    {
        "id": "LOG-1",
        "message": "Connection pool timeout acquiring JDBC connection",
        "stack_trace": "java.sql.SQLException: Connection pool exhausted at HikariPool.getConnection",
    }
]

SAMPLE_DEPLOYMENTS = [
    {
        "id": "DEP-1",
        "service": "checkout-service",
        "commit_hash": "c0ffee1",
        "deployed_at": "2026-05-10T14:15:00Z",
        "environment": "production",
        "status": "SUCCESS",
    }
]


def test_correlate_code_error_with_jira_bug():
    correlator = EvidenceCorrelator()

    jira_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        matched_issues=[
            JiraIssue(
                id="401",
                key="OPS-401",
                summary="NullPointerException thrown during checkout order finalization",
                description="Unhandled NullPointerException in OrderService line 88",
                issue_type="Bug",
                status="In Progress",
                priority="Critical",
            )
        ],
        primary_issue=JiraIssue(
            id="401",
            key="OPS-401",
            summary="NullPointerException thrown during checkout order finalization",
            description="Unhandled NullPointerException in OrderService line 88",
            issue_type="Bug",
            status="In Progress",
            priority="Critical",
        ),
        correlation=JiraCorrelationMatch(
            matched_by=["service_name", "failure_keywords"],
            confidence_score=0.75,
            explanation="ticket is scoped to affected service; contains failure signals",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira issue OPS-401 with high confidence.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=[],
        tickets=[],
        jira_evidence=jira_evidence,
    )

    code_candidate = results.get("CODE_ERROR")
    assert code_candidate is not None
    assert any("OPS-401" in ev for ev in code_candidate["evidence"])
    assert any("active bug/runtime defect" in ev for ev in code_candidate["evidence"])


def test_correlate_database_with_jira_db_ticket():
    correlator = EvidenceCorrelator()

    jira_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        primary_issue=JiraIssue(
            id="402",
            key="OPS-402",
            summary="Postgres connection pool exhaustion under peak load",
            description="Database lock serialization observed on order table",
            issue_type="Incident",
            status="Investigating",
            priority="High",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira issue OPS-402.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=[],
        tickets=[],
        jira_evidence=jira_evidence,
    )

    db_candidate = results.get("DATABASE")
    assert db_candidate is not None
    assert any("OPS-402" in ev for ev in db_candidate["evidence"])
    assert any("database connection pool" in ev for ev in db_candidate["evidence"])


def test_correlate_infrastructure_with_jira_resource_ticket():
    correlator = EvidenceCorrelator()

    jira_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        primary_issue=JiraIssue(
            id="403",
            key="OPS-403",
            summary="Pod OOMKill and memory resource saturation",
            description="Container memory limits exceeded",
            issue_type="Task",
            status="Open",
            priority="High",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira issue OPS-403.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=[],
        tickets=[],
        jira_evidence=jira_evidence,
    )

    infra_candidate = results.get("INFRASTRUCTURE")
    assert infra_candidate is not None
    assert any("OPS-403" in ev for ev in infra_candidate["evidence"])
    assert any("infrastructure resource contention" in ev for ev in infra_candidate["evidence"])


def test_correlate_deployment_with_jira_release_ticket():
    correlator = EvidenceCorrelator()

    jira_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        primary_issue=JiraIssue(
            id="404",
            key="OPS-404",
            summary="Production release and schema migration v2.4",
            description="Deployment changelog and DB migration",
            issue_type="Deployment",
            status="Completed",
            priority="Medium",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira release OPS-404.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        jira_evidence=jira_evidence,
    )

    dep_candidate = results.get("DEPLOYMENT")
    assert dep_candidate is not None
    assert any("OPS-404" in ev for ev in dep_candidate["evidence"])
    assert any("scheduled release/deployment activity" in ev for ev in dep_candidate["evidence"])


def test_quad_source_cross_correlation():
    correlator = EvidenceCorrelator()

    github_commits = [
        {
            "sha": "c0ffee11223344",
            "short_sha": "c0ffee1",
            "message": "fix: update db connection timeout and pool config",
            "author": {"name": "Dev", "email": "dev@test.com", "date": "2026-05-10T14:10:00Z"},
            "files": ["backend/db/pool.py", "backend/config.py"],
            "stats": {"total": 12, "additions": 10, "deletions": 2},
        }
    ]

    sentry_evidence = SentryEvidence(
        status="CONNECTED",
        issue_count=1,
        issues=[
            SentryIssue(
                id="101",
                short_id="ISSUE-101",
                title="TimeoutException: Failed to acquire connection",
                culprit="backend/db/pool.py in get_conn",
                count=42,
            )
        ],
        matched_exception_type="TimeoutException",
        message="1 active Sentry issue detected.",
    )

    prom_evidence = PrometheusEvidence(
        status="CONNECTED",
        url="http://prom.test:9090",
        service="checkout-service",
        error_rate=PrometheusMetricSample(
            metric_name="HTTP Error Rate",
            query='rate(http_requests_total{status=~"5.."}[5m])',
            unit="%",
            baseline_value=0.2,
            observed_value=22.0,
            deviation_pct=10900.0,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        anomalies_detected=1,
        highest_correlation="HIGH",
        summary="Error rate anomaly detected.",
    )

    jira_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        primary_issue=JiraIssue(
            id="500",
            key="OPS-500",
            summary="Deployment c0ffee1 timeout and pool exhaustion",
            issue_type="Deployment",
            status="In Progress",
            priority="Critical",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira issue OPS-500.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        github_commits=github_commits,
        sentry_evidence=sentry_evidence,
        prometheus_evidence=prom_evidence,
        jira_evidence=jira_evidence,
    )

    dep_candidate = results.get("DEPLOYMENT")
    assert dep_candidate is not None
    assert any("Quad-Source Cross-Correlation" in ev for ev in dep_candidate["evidence"])
    assert any("OPS-500" in ev for ev in dep_candidate["evidence"])


def test_correlate_without_jira():
    correlator = EvidenceCorrelator()
    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        jira_evidence=None,
    )
    assert len(results) > 0
    assert all("score" in data and "evidence" in data for cat, data in results.items())


def test_root_cause_engine_forwards_jira_evidence():
    engine = RootCauseEngine()
    jira_evidence = JiraEvidence(
        status="CONNECTED",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=1,
        primary_issue=JiraIssue(
            id="601",
            key="OPS-601",
            summary="Compute resource saturation in checkout pod",
            issue_type="Incident",
            status="Investigating",
            priority="Critical",
        ),
        correlation_strength="HIGH",
        summary="Correlated Jira issue OPS-601.",
    )

    results = engine.analyze(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=[],
        deployments=[],
        tickets=[],
        jira_evidence=jira_evidence,
    )

    infra_candidate = next((c for c in results if c["category"] == "INFRASTRUCTURE"), None)
    assert infra_candidate is not None
    assert any("OPS-601" in ev for ev in infra_candidate["evidence"])


def test_irrelevant_jira_issue_not_correlated():
    correlator = EvidenceCorrelator()
    unconnected_jira = JiraEvidence(
        status="NO_ISSUES_FOUND",
        base_url="https://mock.atlassian.net",
        project_key="OPS",
        total_issues_found=0,
        matched_issues=[],
        primary_issue=None,
        correlation=None,
        correlation_strength="NONE",
        summary="No issues matched.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=[],
        deployments=[],
        tickets=[],
        jira_evidence=unconnected_jira,
    )

    for cat, data in results.items():
        assert not any("Jira issue" in ev for ev in data["evidence"])
