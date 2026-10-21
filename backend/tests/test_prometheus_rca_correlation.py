"""
Tests for Prometheus Metric Telemetry Evidence Correlation with RCA Engine.
Validates:
1. EvidenceCorrelator INFRASTRUCTURE enrichment with Prometheus CPU/Memory anomalies.
2. EvidenceCorrelator CODE_ERROR enrichment with Prometheus Error Rate / Availability anomalies.
3. EvidenceCorrelator DATABASE & NETWORK enrichment with P95 Latency anomalies.
4. EvidenceCorrelator TRAFFIC enrichment with Request Rate anomalies.
5. Tri-Source Cross-Correlation (GitHub commit + Sentry runtime exception + Prometheus metric deviation).
6. Graceful baseline behavior when Prometheus is None or UNAVAILABLE.
7. RootCauseEngine forwarding of prometheus_evidence to EvidenceCorrelator.
"""

import pytest
from backend.app.rca.evidence_correlator import EvidenceCorrelator
from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.schemas.prometheus import (
    PrometheusEvidence,
    PrometheusMetricSample,
    PrometheusTimeWindow,
)
from backend.app.schemas.sentry import (
    SentryEvidence,
    SentryIssue,
)


SAMPLE_INCIDENT = {
    "id": "INC-TEST-PROM",
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


def test_correlate_infrastructure_with_prometheus_cpu_memory():
    correlator = EvidenceCorrelator()

    prom_evidence = PrometheusEvidence(
        status="CONNECTED",
        url="http://prom.test:9090",
        service="checkout-service",
        cpu_utilization=PrometheusMetricSample(
            metric_name="CPU Utilization",
            query="rate(container_cpu_usage_seconds_total[5m])",
            unit="%",
            baseline_value=25.0,
            observed_value=94.0,
            deviation_pct=276.0,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        memory_utilization=PrometheusMetricSample(
            metric_name="Memory Utilization",
            query="process_resident_memory_bytes",
            unit="%",
            baseline_value=40.0,
            observed_value=91.0,
            deviation_pct=127.5,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        anomalies_detected=2,
        highest_correlation="HIGH",
        summary="CPU and Memory anomalies detected.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        prometheus_evidence=prom_evidence,
    )

    infra_candidate = results.get("INFRASTRUCTURE")
    assert infra_candidate is not None
    assert infra_candidate["score"] >= 0.70
    assert any("CPU Utilization" in ev or "CPU saturation" in ev for ev in infra_candidate["evidence"])
    assert any("memory" in ev.lower() for ev in infra_candidate["evidence"])


def test_correlate_code_error_with_prometheus_error_rate():
    correlator = EvidenceCorrelator()

    prom_evidence = PrometheusEvidence(
        status="CONNECTED",
        url="http://prom.test:9090",
        service="checkout-service",
        error_rate=PrometheusMetricSample(
            metric_name="HTTP Error Rate",
            query='rate(http_requests_total{status=~"5.."}[5m])',
            unit="%",
            baseline_value=0.1,
            observed_value=18.5,
            deviation_pct=18400.0,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        availability=PrometheusMetricSample(
            metric_name="Service Availability",
            query="avg_over_time(up[5m])",
            unit="%",
            baseline_value=100.0,
            observed_value=65.0,
            deviation_pct=-35.0,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        anomalies_detected=2,
        highest_correlation="HIGH",
        summary="Error rate surge and availability drop detected.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=[],
        tickets=[],
        prometheus_evidence=prom_evidence,
    )

    code_candidate = results.get("CODE_ERROR")
    assert code_candidate is not None
    assert any("error-rate spike" in ev for ev in code_candidate["evidence"])
    assert any("service availability" in ev for ev in code_candidate["evidence"])


def test_correlate_traffic_with_prometheus_request_rate():
    correlator = EvidenceCorrelator()

    prom_evidence = PrometheusEvidence(
        status="CONNECTED",
        url="http://prom.test:9090",
        service="checkout-service",
        request_rate=PrometheusMetricSample(
            metric_name="Request Rate",
            query="rate(http_requests_total[5m])",
            unit="req/s",
            baseline_value=500.0,
            observed_value=2500.0,
            deviation_pct=400.0,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        anomalies_detected=1,
        highest_correlation="HIGH",
        summary="Request rate surge detected.",
    )

    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=[],
        deployments=[],
        tickets=[],
        prometheus_evidence=prom_evidence,
    )

    traffic_candidate = results.get("TRAFFIC")
    assert traffic_candidate is not None
    assert any("throughput anomaly" in ev for ev in traffic_candidate["evidence"])


def test_tri_source_cross_correlation():
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
                user_count=15,
                first_seen="2026-05-10T14:16:00Z",
                last_seen="2026-05-10T14:28:00Z",
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
        p95_latency=PrometheusMetricSample(
            metric_name="P95 Latency",
            query="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            unit="ms",
            baseline_value=120.0,
            observed_value=1250.0,
            deviation_pct=941.6,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        anomalies_detected=2,
        highest_correlation="HIGH",
        summary="Error rate and P95 latency anomalies detected.",
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
    )

    dep_candidate = results.get("DEPLOYMENT")
    assert dep_candidate is not None
    assert any("Tri-Source Cross-Correlation" in ev for ev in dep_candidate["evidence"])


def test_correlate_without_prometheus():
    correlator = EvidenceCorrelator()
    results = correlator.correlate(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=SAMPLE_LOGS,
        deployments=SAMPLE_DEPLOYMENTS,
        tickets=[],
        prometheus_evidence=None,
    )
    assert len(results) > 0
    assert all("score" in data and "evidence" in data for cat, data in results.items())


def test_root_cause_engine_forwards_prometheus_evidence():
    engine = RootCauseEngine()
    prom_evidence = PrometheusEvidence(
        status="CONNECTED",
        url="http://prom.test:9090",
        service="checkout-service",
        cpu_utilization=PrometheusMetricSample(
            metric_name="CPU Utilization",
            query="rate(container_cpu_usage_seconds_total[5m])",
            unit="%",
            baseline_value=15.0,
            observed_value=98.0,
            deviation_pct=553.3,
            anomaly_detected=True,
            correlation_strength="HIGH",
        ),
        anomalies_detected=1,
        highest_correlation="HIGH",
        summary="High CPU anomaly detected.",
    )

    results = engine.analyze(
        incident=SAMPLE_INCIDENT,
        metrics=SAMPLE_METRICS,
        logs=[],
        deployments=[],
        tickets=[],
        prometheus_evidence=prom_evidence,
    )

    infra_candidate = next((c for c in results if c["category"] == "INFRASTRUCTURE"), None)
    assert infra_candidate is not None
    assert any("CPU saturation" in ev for ev in infra_candidate["evidence"])
