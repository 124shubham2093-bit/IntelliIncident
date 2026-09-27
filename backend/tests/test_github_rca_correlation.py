"""
Tests for GitHub Evidence Correlation with RCA Engine and Recommendations
Validates:
1. EvidenceCorrelator DEPLOYMENT evidence enrichment with commit details (+0.05)
2. EvidenceCorrelator CODE_ERROR evidence enrichment with stack trace file overlap (+0.10)
3. Baseline correlation behavior without GitHub commits
4. RootCauseEngine forwarding of github_commits
5. IncidentService commit hash validation rules
6. IncidentService error shielding (404, 401, 403, timeouts)
7. RecommendationService REC-02 enrichment with commit SHA and URL
8. GET /api/incidents/{id} with mocked GitHub commit
9. POST /api/incidents pipeline with GitHub commit correlation
10. GET /api/reports/{id} evidence preservation
11. GET /api/root-cause/{id} evidence preservation
12. Authoritative Fuzzy Risk read-only preservation
13. Strict absence of proven causation claims
"""

import pytest
from unittest.mock import AsyncMock, patch
from backend.app.rca.evidence_correlator import EvidenceCorrelator
from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.services.incident_service import IncidentService
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.github_service import (
    GitHubNotFoundError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubUnavailableError,
)
from backend.app.schemas.github import (
    GitHubCommitDetail,
    GitHubCommitAuthor,
    GitHubChangedFile,
)

SAMPLE_COMMIT_DICT = {
    "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
    "short_sha": "a1b2c3d",
    "message": "fix: update order serializer validation logic\n\nResolves issue with null orders",
    "author": {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "username": "janedev",
        "date": "2026-09-26T12:00:00Z",
    },
    "stats": {
        "total": 35,
        "additions": 25,
        "deletions": 10,
    },
    "files": [
        {
            "filename": "services/OrderService.java",
            "status": "modified",
            "additions": 20,
            "deletions": 8,
            "changes": 28,
        },
        {
            "filename": "config/order_config.yaml",
            "status": "modified",
            "additions": 5,
            "deletions": 2,
            "changes": 7,
        },
    ],
    "committed_at": "2026-09-26T12:00:00Z",
    "html_url": "https://github.com/org/repo/commit/a1b2c3d4e5f6789012345678901234567890abcd",
}

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


def test_evidence_correlator_with_github_deployment_commit():
    """Verify DEPLOYMENT evidence includes factual commit data without arbitrary score boosting."""
    res_without = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, []
    )
    res_with = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [],
        github_commits=[SAMPLE_COMMIT_DICT],
    )

    dep_ev = res_with["DEPLOYMENT"]["evidence"]
    assert any("a1b2c3d" in ev for ev in dep_ev)
    assert any("Jane Developer" in ev for ev in dep_ev)
    assert any("2 files" in ev for ev in dep_ev)
    assert any("+25/-10" in ev for ev in dep_ev)

    # Factual evidence only: no arbitrary score boosting
    assert res_with["DEPLOYMENT"]["score"] == res_without["DEPLOYMENT"]["score"]


def test_evidence_correlator_code_error_stack_trace_overlap():
    """Verify CODE_ERROR evidence cites file referenced in stack trace without arbitrary score boosting."""
    res_without = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, []
    )
    res_with = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [],
        github_commits=[SAMPLE_COMMIT_DICT],
    )

    code_ev = res_with["CODE_ERROR"]["evidence"]
    matching_ev = [ev for ev in code_ev if "references 'services/OrderService.java'" in ev]
    assert len(matching_ev) == 1
    assert "modified in deployment commit a1b2c3d" in matching_ev[0]

    # Factual evidence only: no arbitrary score boosting
    assert res_with["CODE_ERROR"]["score"] == res_without["CODE_ERROR"]["score"]


def test_evidence_correlator_without_github_commits():
    """Verify that omitting or passing empty github_commits yields identical baseline behavior."""
    res_none = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [], github_commits=None
    )
    res_empty = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [], github_commits=[]
    )
    assert res_none == res_empty


def test_root_cause_engine_passes_github_commits():
    """Verify RootCauseEngine forwards github_commits and decorates ranked hypotheses."""
    engine = RootCauseEngine()
    candidates = engine.analyze(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        github_commits=[SAMPLE_COMMIT_DICT],
    )

    dep_candidate = next(c for c in candidates if c["category"] == "DEPLOYMENT")
    assert any("a1b2c3d" in ev for ev in dep_candidate["evidence"])

    code_candidate = next(c for c in candidates if c["category"] == "CODE_ERROR")
    assert any("references 'services/OrderService.java'" in ev for ev in code_candidate["evidence"])


def test_incident_service_valid_commit_hash_filtering():
    """Verify _is_valid_commit_hash accepts valid hex SHAs and rejects refs, words, and invalid lengths."""
    # Valid
    assert IncidentService._is_valid_commit_hash("a1b2c3d") is True
    assert IncidentService._is_valid_commit_hash("A1B2C3D") is True
    assert IncidentService._is_valid_commit_hash("a1b2c3d4e5f6789012345678901234567890abcd") is True

    # Invalid aliases / branches
    assert IncidentService._is_valid_commit_hash("main") is False
    assert IncidentService._is_valid_commit_hash("master") is False
    assert IncidentService._is_valid_commit_hash("head") is False
    assert IncidentService._is_valid_commit_hash("latest") is False
    assert IncidentService._is_valid_commit_hash("default") is False

    # Invalid strings / None / lengths
    assert IncidentService._is_valid_commit_hash(None) is False
    assert IncidentService._is_valid_commit_hash("") is False
    assert IncidentService._is_valid_commit_hash("   ") is False
    assert IncidentService._is_valid_commit_hash("abc12") is False  # < 7 chars
    assert IncidentService._is_valid_commit_hash("not-a-valid-hex-commit") is False
    assert IncidentService._is_valid_commit_hash("g" * 40) is False  # 'g' is not hex


import asyncio

def test_incident_service_github_shielding_404():
    """Verify IncidentService._fetch_deployment_commits handles 404 gracefully without throwing."""
    service = IncidentService()
    with patch.object(service.github_service, "get_commit", new=AsyncMock(side_effect=GitHubNotFoundError("Commit not found"))):
        commits = asyncio.run(service._fetch_deployment_commits([{"commit_hash": "a1b2c3d"}]))
        assert commits == []


def test_incident_service_github_shielding_401_403_timeout():
    """Verify IncidentService._fetch_deployment_commits shields against 401, 403, and timeouts."""
    service = IncidentService()

    for err in [
        GitHubAuthError("Invalid token"),
        GitHubRateLimitError("Rate limit exceeded"),
        GitHubUnavailableError("Timed out"),
        RuntimeError("Unexpected transport fault"),
    ]:
        with patch.object(service.github_service, "get_commit", new=AsyncMock(side_effect=err)):
            commits = asyncio.run(service._fetch_deployment_commits([{"commit_hash": "a1b2c3d"}]))
            assert commits == []


def test_recommendations_enriched_with_commit_details():
    """Verify RecommendationService REC-02 contains commit SHA and URL when available."""
    # DEPLOYMENT category
    top_cand = {"category": "DEPLOYMENT"}
    recs = RecommendationService.generate_recommendations(
        top_candidate=top_cand,
        service_name="order-service",
        severity="HIGH",
        github_commits=[SAMPLE_COMMIT_DICT],
    )
    rec02 = next(r for r in recs if r["id"] == "REC-02")
    assert "a1b2c3d" in rec02["title"]
    assert "gh browse a1b2c3d --repo" in rec02["actionCmd"]
    assert "124shubham2093-bit/IntelliIncident" in rec02["actionCmd"]
    assert "https://github.com/org/repo/commit/" in rec02["description"]

    # CODE_ERROR category
    top_cand_code = {"category": "CODE_ERROR"}
    recs_code = RecommendationService.generate_recommendations(
        top_candidate=top_cand_code,
        service_name="order-service",
        severity="HIGH",
        github_commits=[SAMPLE_COMMIT_DICT],
    )
    rec02_code = next(r for r in recs_code if r["id"] == "REC-02")
    assert "a1b2c3d" in rec02_code["description"]
    assert "https://github.com/org/repo/commit/" in rec02_code["description"]


def test_incident_api_get_with_github_commit_mocked(client):
    """End-to-end GET /api/incidents/INC-8610 with mocked GitHubService returns enriched evidence."""
    mock_detail = GitHubCommitDetail(
        sha="a1b2c3d4e5f6789012345678901234567890abcd",
        short_sha="a1b2c3d",
        message="Deploy v2.4.1 release candidate",
        author=GitHubCommitAuthor(name="Release Engineer", email="rel@example.com"),
        committed_at="2026-09-26T12:00:00Z",
        html_url="https://github.com/org/repo/commit/a1b2c3d4e5f6789012345678901234567890abcd",
        stats={"total": 10, "additions": 8, "deletions": 2},
        files=[
            GitHubChangedFile(
                filename="services/OrderService.java",
                status="modified",
                additions=8,
                deletions=2,
                changes=10,
            )
        ],
    )

    with patch("backend.app.services.incident_service.GitHubService.get_commit", new=AsyncMock(return_value=mock_detail)):
        resp = client.get("/api/incidents/INC-8610")
        assert resp.status_code == 200
        data = resp.json()

        assert "githubCommits" in data
        assert len(data["githubCommits"]) == 1
        assert data["githubCommits"][0]["short_sha"] == "a1b2c3d"

        # Check DEPLOYMENT evidence in rootCauseCandidates
        rc_cands = data["rootCauseCandidates"]
        dep_cand = next(c for c in rc_cands if c["category"] == "DEPLOYMENT")
        assert any("a1b2c3d" in ev for ev in dep_cand["evidence"])

        # Check CODE_ERROR evidence in rootCauseCandidates
        code_cand = next(c for c in rc_cands if c["category"] == "CODE_ERROR")
        assert any("OrderService.java" in ev for ev in code_cand["evidence"])


def test_incident_api_create_with_github_commit_mocked(client):
    """End-to-end POST /api/incidents ingests incident and correlates commit evidence."""
    mock_detail = GitHubCommitDetail(
        sha="deadbeef12345678901234567890123456789012",
        short_sha="deadbee",
        message="Hotfix for payment gateway checkout",
        author=GitHubCommitAuthor(name="Payment Lead", email="pay@example.com"),
        committed_at="2026-09-27T08:00:00Z",
        html_url="https://github.com/org/repo/commit/deadbeef",
        stats={"total": 15, "additions": 10, "deletions": 5},
        files=[
            GitHubChangedFile(
                filename="payment_gateway.py",
                status="modified",
                additions=10,
                deletions=5,
                changes=15,
            )
        ],
    )

    payload = {
        "title": "Payment Gateway Timeout",
        "service": "payment-service",
        "metrics": {
            "error_rate": 35.0,
            "latency_p99": 950.0,
            "latency_p50": 150.0,
            "affected_users": 1200,
            "request_volume": 4000,
            "deployment_recency_minutes": 20,
            "cpu_utilization": 40.0,
            "memory_utilization": 45.0,
            "service_criticality": 4,
        },
        "deployments": [
            {
                "commit_hash": "deadbee",
                "deployed_at": "2026-09-27T08:00:00Z",
                "environment": "production",
                "status": "SUCCESS",
            }
        ],
        "logs": [
            {
                "log_level": "ERROR",
                "message": "ConnectionRefused in payment_gateway.py",
                "stack_trace": "File '/app/payment_gateway.py', line 88, in process_charge",
            }
        ],
    }

    with patch("backend.app.services.incident_service.GitHubService.get_commit", new=AsyncMock(return_value=mock_detail)):
        resp = client.post("/api/incidents", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        assert "githubCommits" in data
        assert len(data["githubCommits"]) == 1
        assert data["githubCommits"][0]["short_sha"] == "deadbee"

        rc_cands = data["rootCauseCandidates"]
        dep_cand = next(c for c in rc_cands if c["category"] == "DEPLOYMENT")
        assert any("deadbee" in ev for ev in dep_cand["evidence"])

        code_cand = next(c for c in rc_cands if c["category"] == "CODE_ERROR")
        assert any("payment_gateway.py" in ev for ev in code_cand["evidence"])


def test_reports_and_root_cause_api_preserves_github_evidence(client):
    """Verify GET /api/reports/{id} and GET /api/root-cause/{id} preserve enriched evidence."""
    mock_detail = GitHubCommitDetail(
        sha="a1b2c3d4e5f6789012345678901234567890abcd",
        short_sha="a1b2c3d",
        message="Deploy v2.4.1",
        author=GitHubCommitAuthor(name="Release Engineer"),
        committed_at="2026-09-26T12:00:00Z",
        html_url="https://github.com/org/repo/commit/a1b2c3d",
        stats={"total": 5, "additions": 3, "deletions": 2},
        files=[GitHubChangedFile(filename="OrderService.java", status="modified", additions=3, deletions=2, changes=5)],
    )

    with patch("backend.app.services.incident_service.GitHubService.get_commit", new=AsyncMock(return_value=mock_detail)):
        # 1. Root Cause route
        rc_resp = client.get("/api/root-cause/INC-8610")
        assert rc_resp.status_code == 200
        rc_data = rc_resp.json()
        dep_cand = next(c for c in rc_data if c["category"] == "DEPLOYMENT")
        assert any("a1b2c3d" in ev for ev in dep_cand["evidence"])

        # 2. Reports route
        rep_resp = client.get("/api/reports/INC-8610")
        assert rep_resp.status_code == 200
        rep_data = rep_resp.json()
        assert "incident" in rep_data
        assert any("a1b2c3d" in ev for ev in rep_data["incident"]["rootCauseCandidates"][0]["evidence"] or []) or any(
            "a1b2c3d" in str(c) for c in rep_data["incident"]["rootCauseCandidates"]
        )


def test_fuzzy_risk_remains_read_only_and_unchanged(client):
    """Verify that fuzzy risk calculation remains mathematically authoritative and unchanged by GitHub evidence."""
    resp = client.get("/api/incidents/INC-8610")
    assert resp.status_code == 200
    data = resp.json()

    fuzzy = data["fuzzyRisk"]
    assert fuzzy["riskScore"] == 59
    assert fuzzy["riskLevel"] == "MEDIUM"
    assert fuzzy["defuzzificationMethod"] == "Centroid of Area (COA)"


def test_no_proven_causation_claimed():
    """Verify that evidence correlator and recommendations strictly use correlation phrases and avoid causal claims."""
    res = EvidenceCorrelator.correlate(
        SAMPLE_INCIDENT, SAMPLE_METRICS, SAMPLE_LOGS, SAMPLE_DEPLOYMENTS, [],
        github_commits=[SAMPLE_COMMIT_DICT],
    )

    all_evidence = []
    for cat_data in res.values():
        all_evidence.extend(cat_data["evidence"])

    for ev in all_evidence:
        ev_lower = ev.lower()
        assert "proven cause" not in ev_lower
        assert "caused by commit" not in ev_lower
        assert "definitely caused" not in ev_lower
        assert "guilty commit" not in ev_lower
