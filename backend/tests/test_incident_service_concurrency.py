import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from backend.app.services.incident_service import IncidentService
from backend.app.schemas.sentry import SentryEvidence
from backend.app.schemas.prometheus import PrometheusEvidence
from backend.app.schemas.jira import JiraEvidence
from backend.app.schemas.incident import IncidentCreatePayload


@pytest.mark.anyio
async def test_get_incident_details_concurrent_evidence_execution():
    """
    Verify that get_incident_details executes the three external evidence calls
    (Prometheus, Sentry, Jira) concurrently via asyncio.gather and passes the
    exact returned evidence objects unchanged to RootCauseEngine.analyze and serialization.
    """
    service = IncidentService()

    active_calls = 0
    max_active_calls = 0

    mock_sentry_ev = SentryEvidence(
        status="CONNECTED",
        message="Sentry test evidence",
        issue_count=1,
    )
    mock_prom_ev = PrometheusEvidence(
        status="AVAILABLE",
        url="http://localhost:9090",
        service="order-processing-service",
        summary="Test prometheus evidence",
        anomalies_detected=1,
    )
    mock_jira_ev = JiraEvidence(
        status="AVAILABLE",
        base_url="https://jira.company.com",
        summary="Test jira evidence",
        total_issues_found=2,
    )

    async def mock_sentry(**kwargs):
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0.04)
        active_calls -= 1
        return mock_sentry_ev

    async def mock_prometheus(**kwargs):
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0.04)
        active_calls -= 1
        return mock_prom_ev

    async def mock_jira(**kwargs):
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0.04)
        active_calls -= 1
        return mock_jira_ev

    service.sentry_service.get_runtime_evidence = AsyncMock(side_effect=mock_sentry)
    service.prometheus_service.get_incident_metric_evidence = AsyncMock(side_effect=mock_prometheus)
    service.jira_service.get_incident_jira_evidence = AsyncMock(side_effect=mock_jira)

    captured_rca_kwargs = {}
    original_analyze = service.root_cause_engine.analyze

    def mock_analyze(**kwargs):
        captured_rca_kwargs.update(kwargs)
        return original_analyze(**kwargs)

    service.root_cause_engine.analyze = MagicMock(side_effect=mock_analyze)

    # INC-8610 is seeded in the test sqlite database by conftest.py
    details = await service.get_incident_details("INC-8610")

    assert details is not None
    assert details["id"] == "INC-8610"

    # Concurrency verification: all 3 evidence calls must have run at the same time
    assert max_active_calls == 3, f"Expected 3 concurrent calls, observed max {max_active_calls}"

    # Downstream RCA verification: evidence objects passed unchanged
    assert captured_rca_kwargs["sentry_evidence"] is mock_sentry_ev
    assert captured_rca_kwargs["prometheus_evidence"] is mock_prom_ev
    assert captured_rca_kwargs["jira_evidence"] is mock_jira_ev

    # Serialization verification: dumped evidence present in final dict
    assert details["sentryEvidence"] == mock_sentry_ev.model_dump()
    assert details["prometheusEvidence"] == mock_prom_ev.model_dump()
    assert details["jiraEvidence"] == mock_jira_ev.model_dump()


@pytest.mark.anyio
async def test_create_incident_concurrent_evidence_execution():
    """
    Verify that create_incident executes the three external evidence calls concurrently
    via asyncio.gather and passes the exact returned evidence to RootCauseEngine.analyze.
    """
    service = IncidentService()

    active_calls = 0
    max_active_calls = 0

    mock_sentry_ev = SentryEvidence(status="NO_ISSUES_FOUND", message="Clean Sentry")
    mock_prom_ev = PrometheusEvidence(
        status="AVAILABLE",
        url="http://localhost:9090",
        service="payment-service",
        summary="Test prometheus evidence",
    )
    mock_jira_ev = JiraEvidence(
        status="AVAILABLE",
        base_url="https://jira.company.com",
        summary="Test jira evidence",
        total_issues_found=0,
    )

    async def mock_sentry(**kwargs):
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0.04)
        active_calls -= 1
        return mock_sentry_ev

    async def mock_prometheus(**kwargs):
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0.04)
        active_calls -= 1
        return mock_prom_ev

    async def mock_jira(**kwargs):
        nonlocal active_calls, max_active_calls
        active_calls += 1
        max_active_calls = max(max_active_calls, active_calls)
        await asyncio.sleep(0.04)
        active_calls -= 1
        return mock_jira_ev

    service.sentry_service.get_runtime_evidence = AsyncMock(side_effect=mock_sentry)
    service.prometheus_service.get_incident_metric_evidence = AsyncMock(side_effect=mock_prometheus)
    service.jira_service.get_incident_jira_evidence = AsyncMock(side_effect=mock_jira)

    captured_rca_kwargs = {}
    original_analyze = service.root_cause_engine.analyze

    def mock_analyze(**kwargs):
        captured_rca_kwargs.update(kwargs)
        return original_analyze(**kwargs)

    service.root_cause_engine.analyze = MagicMock(side_effect=mock_analyze)

    payload = IncidentCreatePayload(
        id="INC-CONCURRENT-TEST-1",
        title="Concurrent Pipeline Test Incident",
        service="payment-service",
        summary="Testing concurrent evidence collection during incident creation",
        status="OPEN",
    )

    created = await service.create_incident(payload)

    assert created is not None
    assert created["id"] == "INC-CONCURRENT-TEST-1"

    # Concurrency verification: all 3 evidence calls must have run at the same time
    assert max_active_calls == 3, f"Expected 3 concurrent calls in create_incident, observed max {max_active_calls}"

    # Downstream RCA verification: evidence objects passed unchanged
    assert captured_rca_kwargs["sentry_evidence"] is mock_sentry_ev
    assert captured_rca_kwargs["prometheus_evidence"] is mock_prom_ev
    assert captured_rca_kwargs["jira_evidence"] is mock_jira_ev
