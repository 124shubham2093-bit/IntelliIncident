"""
Unit tests for PrometheusService (Prometheus Metric Telemetry Integration).
All tests mock the HTTP/network layer using AsyncMock/httpx and require no real Prometheus instance.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from backend.app.services.prometheus_service import (
    PrometheusService,
    DEFAULT_PROMQL_QUERIES,
)
from backend.app.schemas.prometheus import (
    PrometheusStatusResponse,
    PrometheusMetricSample,
    PrometheusEvidence,
    PrometheusTimeWindow,
)


@pytest.mark.anyio
async def test_prometheus_service_init_defaults(monkeypatch):
    monkeypatch.setattr("backend.app.services.prometheus_service.settings.PROMETHEUS_URL", "http://prometheus.local:9090")
    service = PrometheusService()
    assert service.url == "http://prometheus.local:9090"
    assert service.timeout == 4.0


@pytest.mark.anyio
async def test_prometheus_service_unconfigured():
    service = PrometheusService(url="")
    status = await service.get_health()
    assert status.status == "NOT_CONFIGURED"
    assert status.reachable is False
    assert "not configured" in status.message.lower()


@pytest.mark.anyio
async def test_prometheus_service_health_connected():
    mock_build_resp = MagicMock()
    mock_build_resp.status_code = 200
    mock_build_resp.json.return_value = {
        "status": "success",
        "data": {"version": "2.45.0", "revision": "abc1234"}
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_build_resp)

    service = PrometheusService(url="http://prom.test:9090", client=mock_client)
    status = await service.get_health()

    assert status.status == "CONNECTED"
    assert status.reachable is True
    assert status.version == "2.45.0"
    assert "operational" in status.message.lower()


@pytest.mark.anyio
async def test_prometheus_service_health_unavailable():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

    service = PrometheusService(url="http://prom.down:9090", client=mock_client)
    status = await service.get_health()

    assert status.status == "UNAVAILABLE"
    assert status.reachable is False
    assert "unreachable" in status.message.lower()


@pytest.mark.anyio
async def test_prometheus_service_query_instant():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"service": "order-service", "instance": "pod-1"},
                    "value": [1700000000.0, "78.5"]
                }
            ]
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = PrometheusService(url="http://prom.test:9090", client=mock_client)
    val = await service.query_instant('rate(http_requests_total{service="order-service"}[5m])')

    assert val == 78.5


@pytest.mark.anyio
async def test_prometheus_service_query_range():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"service": "payment-service"},
                    "values": [
                        [1700000000.0, "12.0"],
                        [1700000060.0, "15.0"],
                        [1700000120.0, "14.5"]
                    ]
                }
            ]
        }
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    service = PrometheusService(url="http://prom.test:9090", client=mock_client)
    points = await service.query_range(
        query='process_cpu_usage{service="payment-service"}',
        start=1700000000.0,
        end=1700000120.0,
        step="60s",
    )

    assert len(points) == 3
    assert points[0].value == 12.0
    assert points[1].value == 15.0
    assert points[2].value == 14.5


def test_derive_time_window():
    service = PrometheusService()
    incident_ts = "2026-05-10T14:30:00Z"
    tw, b_start, b_end, i_start, i_end = service.derive_time_window(incident_ts)

    assert isinstance(tw, PrometheusTimeWindow)
    assert "2026-05-10T14:30:00" in tw.incident_time
    assert tw.baseline_start < tw.baseline_end
    assert tw.baseline_end <= tw.incident_start
    assert tw.incident_start < tw.incident_end
    assert b_start < b_end
    assert b_end <= i_start
    assert i_start < i_end


def test_analyze_metric_deviation_normal():
    service = PrometheusService()
    anomaly, dev_pct, strength = service.analyze_metric_deviation(
        baseline=50.0,
        observed=52.0,
        metric_key="cpu_utilization",
    )

    assert anomaly is False
    assert strength == "NONE"
    assert dev_pct is not None
    assert dev_pct == 4.0


def test_analyze_metric_deviation_spike_anomaly():
    service = PrometheusService()
    anomaly, dev_pct, strength = service.analyze_metric_deviation(
        baseline=0.5,
        observed=18.0,
        metric_key="error_rate",
    )

    assert anomaly is True
    assert strength == "HIGH"
    assert dev_pct is not None
    assert dev_pct > 100.0


def test_analyze_metric_deviation_availability_drop():
    service = PrometheusService()
    anomaly, dev_pct, strength = service.analyze_metric_deviation(
        baseline=99.9,
        observed=60.0,
        metric_key="availability",
    )

    assert anomaly is True
    assert strength == "HIGH"
    assert dev_pct is not None
    assert dev_pct < -20.0


@pytest.mark.anyio
async def test_get_incident_metric_evidence_unavailable():
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Prometheus unreachable"))

    service = PrometheusService(url="http://prom.down:9090", client=mock_client)
    evidence = await service.get_incident_metric_evidence(service="auth-service")

    assert evidence.status == "UNAVAILABLE"
    assert evidence.anomalies_detected == 0
    assert evidence.highest_correlation == "NONE"
    assert "unreachable" in evidence.summary.lower()


@pytest.mark.anyio
async def test_get_incident_metric_evidence_correlated():
    mock_buildinfo_resp = MagicMock()
    mock_buildinfo_resp.status_code = 200
    mock_buildinfo_resp.json.return_value = {
        "status": "success",
        "data": {"version": "2.45.0"}
    }

    async def mock_get(url, params=None, **kwargs):
        if "buildinfo" in url:
            return mock_buildinfo_resp
        if "/api/v1/query_range" in url:
            q = (params or {}).get("query", "")
            if "cpu" in q.lower():
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "status": "success",
                        "data": {
                            "resultType": "matrix",
                            "result": [{
                                "values": [
                                    [1778419800.0, "20.0"],
                                    [1778420400.0, "22.0"],
                                    [1778423000.0, "88.0"],
                                    [1778423600.0, "92.0"],
                                ]
                            }]
                        }
                    }
                )
            return MagicMock(
                status_code=200,
                json=lambda: {
                    "status": "success",
                    "data": {
                        "resultType": "matrix",
                        "result": [{
                            "values": [
                                [1778419800.0, "10.0"],
                                [1778423000.0, "10.5"],
                            ]
                        }]
                    }
                }
            )
        if "/api/v1/query" in url:
            q = (params or {}).get("query", "")
            t = float((params or {}).get("time", 0.0))
            if "cpu" in q.lower():
                val = "90.0" if t > 1778422500.0 else "21.0"
            else:
                val = "10.0"
            return MagicMock(
                status_code=200,
                json=lambda: {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [{"metric": {}, "value": [t, val]}]
                    }
                }
            )
        return mock_buildinfo_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=mock_get)

    service = PrometheusService(url="http://prom.test:9090", client=mock_client)
    evidence = await service.get_incident_metric_evidence(
        service="order-service",
        incident_timestamp="2026-05-10T14:30:00Z"
    )

    assert evidence.status == "CONNECTED"
    assert evidence.service == "order-service"
    assert evidence.anomalies_detected >= 1
    assert evidence.cpu_utilization is not None
    assert evidence.cpu_utilization.anomaly_detected is True
    assert evidence.highest_correlation in ("HIGH", "MEDIUM")
