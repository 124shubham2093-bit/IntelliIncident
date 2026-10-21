"""
Prometheus Metrics Intelligence Service for IntelliIncident.
Provides normalized, read-only access to the Prometheus HTTP API (v1) for
retrieving system and application metrics, evaluating incident time-window baselines,
detecting statistical deviations, and feeding metric evidence into RCA.
STRICTLY READ-ONLY: Never modifies Prometheus configuration or alert rules.
"""

from typing import List, Optional, Dict, Any, Tuple
import datetime
import math
import httpx

from backend.app.core.config import settings
from backend.app.schemas.prometheus import (
    PrometheusStatusResponse,
    PrometheusSeriesPoint,
    PrometheusTimeWindow,
    PrometheusMetricSample,
    PrometheusEvidence,
)

_UNSET = object()

# Default PromQL query templates with {service} parameterization
DEFAULT_PROMQL_QUERIES: Dict[str, Dict[str, str]] = {
    "cpu_utilization": {
        "primary": 'sum(rate(container_cpu_usage_seconds_total{container="{service}"}[5m])) * 100',
        "fallback": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
        "unit": "%",
    },
    "memory_utilization": {
        "primary": '(sum(container_memory_working_set_bytes{container="{service}"}) / sum(container_spec_memory_limit_bytes{container="{service}"})) * 100',
        "fallback": '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
        "unit": "%",
    },
    "request_rate": {
        "primary": 'sum(rate(http_requests_total{service="{service}"}[5m]))',
        "fallback": 'sum(rate(http_requests_total[5m]))',
        "unit": "req/s",
    },
    "error_rate": {
        "primary": '(sum(rate(http_requests_total{service="{service}",status=~"5.."}[5m])) / clamp_min(sum(rate(http_requests_total{service="{service}"}[5m])), 0.001)) * 100',
        "fallback": '(sum(rate(http_requests_total{status=~"5.."}[5m])) / clamp_min(sum(rate(http_requests_total[5m])), 0.001)) * 100',
        "unit": "%",
    },
    "p95_latency": {
        "primary": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="{service}"}[5m])) by (le)) * 1000',
        "fallback": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000',
        "unit": "ms",
    },
    "availability": {
        "primary": 'avg_over_time(up{job="{service}"}[5m]) * 100',
        "fallback": 'avg_over_time(up[5m]) * 100',
        "unit": "%",
    },
}

PROMETHEUS_METRIC_QUERIES = DEFAULT_PROMQL_QUERIES


class PrometheusService:
    """
    Client service for querying the official Prometheus HTTP API v1.
    Normalizes time-series metrics into structured evidence comparing
    pre-incident baselines with incident-window observations.
    """

    def __init__(
        self,
        base_url: Any = _UNSET,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 4.0,
        custom_queries: Optional[Dict[str, Dict[str, str]]] = None,
        url: Any = _UNSET,
    ):
        target_url = url if url is not _UNSET else base_url
        resolved_url = settings.PROMETHEUS_URL if target_url is _UNSET else target_url
        self.base_url = (resolved_url or "").rstrip("/")
        self.url = self.base_url
        self._client = client
        self.timeout = timeout
        self.queries = {**DEFAULT_PROMQL_QUERIES, **(custom_queries or {})}

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "User-Agent": "IntelliIncident-PrometheusIntegration/1.0",
        }

    async def get_health(self) -> PrometheusStatusResponse:
        """
        Check reachability and connectivity to Prometheus HTTP API.
        Safe method that never raises unhandled exceptions.
        """
        if not self.base_url or not self.base_url.strip():
            return PrometheusStatusResponse(
                status="NOT_CONFIGURED",
                url="",
                reachable=False,
                version=None,
                message="Prometheus URL is not configured.",
            )

        endpoint = f"{self.base_url}/api/v1/status/buildinfo"
        try:
            if self._client:
                resp = await self._client.get(endpoint, headers=self._get_headers(), timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(endpoint, headers=self._get_headers())

            if resp.status_code == 200:
                data = resp.json()
                version = data.get("data", {}).get("version") if isinstance(data, dict) else None
                return PrometheusStatusResponse(
                    status="CONNECTED",
                    url=self.base_url,
                    reachable=True,
                    version=version,
                    message="Prometheus server connected and operational.",
                )
            else:
                return PrometheusStatusResponse(
                    status="UNAVAILABLE",
                    url=self.base_url,
                    reachable=False,
                    version=None,
                    message=f"Prometheus returned HTTP {resp.status_code}: {resp.text[:120]}",
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            return PrometheusStatusResponse(
                status="UNAVAILABLE",
                url=self.base_url,
                reachable=False,
                version=None,
                message=f"Prometheus server unreachable at {self.base_url}: {str(e)[:100]}",
            )
        except Exception as e:
            return PrometheusStatusResponse(
                status="ERROR",
                url=self.base_url,
                reachable=False,
                version=None,
                message=f"Error connecting to Prometheus: {str(e)[:100]}",
            )

    async def query_instant(self, query: str, time: Optional[float] = None) -> Optional[float]:
        """
        Execute an instant vector query against GET /api/v1/query.
        Returns the scalar float value if present and finite, or None.
        """
        if not self.base_url:
            return None

        endpoint = f"{self.base_url}/api/v1/query"
        params: Dict[str, Any] = {"query": query}
        if time is not None:
            params["time"] = f"{time:.3f}"

        try:
            if self._client:
                resp = await self._client.get(endpoint, params=params, headers=self._get_headers(), timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(endpoint, params=params, headers=self._get_headers())

            if resp.status_code != 200:
                return None

            body = resp.json()
            if not isinstance(body, dict) or body.get("status") != "success":
                return None

            data = body.get("data", {})
            result_type = data.get("resultType")
            results = data.get("result", [])

            if not results or not isinstance(results, list):
                return None

            # Handle vector result: [{"metric": {...}, "value": [1729000000.0, "42.5"]}]
            first = results[0]
            if result_type == "vector" and "value" in first and len(first["value"]) >= 2:
                raw_val = first["value"][1]
                val = float(raw_val)
                return val if not math.isnan(val) and not math.isinf(val) else None
            # Handle scalar result: [1729000000.0, "42.5"]
            elif result_type == "scalar" and len(results) >= 2:
                val = float(results[1])
                return val if not math.isnan(val) and not math.isinf(val) else None

            return None
        except Exception:
            return None

    async def query_range(
        self, query: str, start: float, end: float, step: int = 60
    ) -> List[PrometheusSeriesPoint]:
        """
        Execute a range query against GET /api/v1/query_range.
        Returns a list of PrometheusSeriesPoint.
        """
        if not self.base_url:
            return []

        endpoint = f"{self.base_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": f"{start:.3f}",
            "end": f"{end:.3f}",
            "step": str(step),
        }

        try:
            if self._client:
                resp = await self._client.get(endpoint, params=params, headers=self._get_headers(), timeout=self.timeout)
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(endpoint, params=params, headers=self._get_headers())

            if resp.status_code != 200:
                return []

            body = resp.json()
            results = body.get("data", {}).get("result", [])
            if not results or not isinstance(results, list):
                return []

            first = results[0]
            raw_values = first.get("values", [])
            points: List[PrometheusSeriesPoint] = []
            for item in raw_values:
                if len(item) >= 2:
                    try:
                        ts = float(item[0])
                        val = float(item[1])
                        if not math.isnan(val) and not math.isinf(val):
                            points.append(PrometheusSeriesPoint(timestamp=ts, value=round(val, 2)))
                    except (ValueError, TypeError):
                        continue
            return points
        except Exception:
            return []

    @staticmethod
    def derive_time_window(incident_timestamp: Optional[str] = None) -> Tuple[PrometheusTimeWindow, float, float, float, float]:
        """
        Derive factual pre-incident baseline and incident-window timestamps.
        Baseline: [T - 60min, T - 15min]
        Incident Window: [T - 15min, T + 30min]
        Returns (PrometheusTimeWindow, baseline_start_epoch, baseline_end_epoch, incident_start_epoch, incident_end_epoch)
        """
        ref_dt = None
        if incident_timestamp:
            clean_ts = incident_timestamp.strip().replace("Z", "+00:00")
            try:
                ref_dt = datetime.datetime.fromisoformat(clean_ts)
            except Exception:
                try:
                    ref_dt = datetime.datetime.strptime(incident_timestamp[:19], "%Y-%m-%dT%H:%M:%S")
                    ref_dt = ref_dt.replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    ref_dt = datetime.datetime.now(datetime.timezone.utc)
        else:
            ref_dt = datetime.datetime.now(datetime.timezone.utc)

        if ref_dt.tzinfo is None:
            ref_dt = ref_dt.replace(tzinfo=datetime.timezone.utc)

        t_epoch = ref_dt.timestamp()

        # Pre-incident baseline: 60m before to 15m before
        b_start_epoch = t_epoch - (60 * 60)
        b_end_epoch = t_epoch - (15 * 60)

        # Incident window: 15m before to 30m after
        i_start_epoch = t_epoch - (15 * 60)
        i_end_epoch = t_epoch + (30 * 60)

        fmt = lambda ep: datetime.datetime.fromtimestamp(ep, tz=datetime.timezone.utc).isoformat()

        tw = PrometheusTimeWindow(
            incident_time=ref_dt.isoformat(),
            baseline_start=fmt(b_start_epoch),
            baseline_end=fmt(b_end_epoch),
            incident_start=fmt(i_start_epoch),
            incident_end=fmt(i_end_epoch),
        )
        return tw, b_start_epoch, b_end_epoch, i_start_epoch, i_end_epoch

    @staticmethod
    def analyze_metric_deviation(
        baseline: Optional[float],
        observed: Optional[float],
        metric_key: str,
    ) -> Tuple[bool, Optional[float], str]:
        """
        Perform lightweight, deterministic statistical deviation analysis.
        Returns: (anomaly_detected: bool, deviation_pct: Optional[float], correlation_strength: str)
        """
        if observed is None:
            return False, None, "NONE"

        # Calculate percentage deviation if baseline exists and is non-zero
        deviation_pct = None
        if baseline is not None:
            if abs(baseline) > 1e-4:
                deviation_pct = round(((observed - baseline) / abs(baseline)) * 100.0, 1)
            else:
                deviation_pct = round(observed * 100.0, 1)

        anomaly = False
        strength = "NONE"

        if metric_key == "cpu_utilization":
            # Baseline vs surge: saturated above 80% or jumped > 25 percentage points
            diff = observed - (baseline if baseline is not None else 0.0)
            if observed >= 85.0 or (baseline is not None and diff >= 25.0):
                anomaly = True
                strength = "HIGH" if observed >= 88.0 or diff >= 35.0 else "MEDIUM"
            elif observed >= 70.0:
                anomaly = True
                strength = "LOW"

        elif metric_key == "memory_utilization":
            diff = observed - (baseline if baseline is not None else 0.0)
            if observed >= 85.0 or (baseline is not None and diff >= 30.0):
                anomaly = True
                strength = "HIGH" if observed >= 88.0 else "MEDIUM"
            elif observed >= 75.0:
                anomaly = True
                strength = "LOW"

        elif metric_key == "error_rate":
            diff = observed - (baseline if baseline is not None else 0.0)
            if observed >= 10.0 or (baseline is not None and diff >= 4.0):
                anomaly = True
                strength = "HIGH" if observed >= 15.0 or diff >= 8.0 else "MEDIUM"
            elif observed >= 3.0:
                anomaly = True
                strength = "LOW"

        elif metric_key == "p95_latency":
            ratio = (observed / max(baseline, 1.0)) if baseline is not None else 1.0
            if observed >= 1200.0 or ratio >= 2.5:
                anomaly = True
                strength = "HIGH" if observed >= 2000.0 or ratio >= 3.5 else "MEDIUM"
            elif observed >= 800.0 or ratio >= 1.8:
                anomaly = True
                strength = "LOW"

        elif metric_key == "request_rate":
            ratio = (observed / max(baseline, 1.0)) if baseline is not None else 1.0
            if ratio >= 2.5 or (baseline is not None and ratio <= 0.25):
                anomaly = True
                strength = "MEDIUM"
            elif ratio >= 1.75 or (baseline is not None and ratio <= 0.5):
                anomaly = True
                strength = "LOW"

        elif metric_key == "availability":
            if observed < 95.0:
                anomaly = True
                strength = "HIGH"
            elif observed < 99.0:
                anomaly = True
                strength = "MEDIUM"

        return anomaly, deviation_pct, strength

    async def get_incident_metric_evidence(
        self,
        service: str,
        incident_timestamp: Optional[str] = None,
    ) -> PrometheusEvidence:
        """
        Execute end-to-end telemetry retrieval across the incident time window.
        Returns a complete, typed PrometheusEvidence object.
        Gracefully handles missing or unreachable Prometheus without throwing.
        """
        health = await self.get_health()
        if not health.reachable:
            return PrometheusEvidence(
                status=health.status,
                url=self.base_url,
                service=service,
                time_window=None,
                metrics={},
                anomalies_detected=0,
                highest_correlation="NONE",
                summary=f"Prometheus is {health.status.lower()}: {health.message}",
            )

        tw, b_start, b_end, i_start, i_end = self.derive_time_window(incident_timestamp)

        # Baseline evaluation midpoint and Incident window evaluation midpoint
        b_mid = (b_start + b_end) / 2.0
        i_mid = (i_start + i_end) / 2.0

        samples: Dict[str, PrometheusMetricSample] = {}
        anomalies_count = 0
        correlation_rank = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
        max_rank = 0

        for key, conf in self.queries.items():
            primary_q = conf["primary"].replace("{service}", service)
            fallback_q = conf.get("fallback", "").replace("{service}", service)
            unit = conf.get("unit", "")

            # Query baseline value
            b_val = await self.query_instant(primary_q, time=b_mid)
            active_q = primary_q
            if b_val is None and fallback_q:
                b_val = await self.query_instant(fallback_q, time=b_mid)
                if b_val is not None:
                    active_q = fallback_q

            # Query incident value
            i_val = await self.query_instant(active_q, time=i_mid)
            if i_val is None and active_q != primary_q:
                i_val = await self.query_instant(primary_q, time=i_mid)
                if i_val is not None:
                    active_q = primary_q

            # Query series points across [b_start, i_end]
            series_pts = await self.query_range(active_q, start=b_start, end=i_end, step=120)

            # Fallback to computing baseline and incident values from range points if instant query returned None
            if b_val is None and series_pts:
                b_pts = [p.value for p in series_pts if b_start <= p.timestamp <= b_end]
                if b_pts:
                    b_val = round(sum(b_pts) / len(b_pts), 2)
            if i_val is None and series_pts:
                i_pts = [p.value for p in series_pts if i_start <= p.timestamp <= i_end]
                if i_pts:
                    i_val = round(sum(i_pts) / len(i_pts), 2)

            if b_val is None and i_val is None and not series_pts:
                samples[key] = PrometheusMetricSample(
                    metric_name=key,
                    query=active_q,
                    unit=unit,
                    baseline_value=None,
                    observed_value=None,
                    deviation_pct=None,
                    anomaly_detected=False,
                    correlation_strength="NONE",
                    status="NOT_FOUND",
                    message=f"No data returned for metric '{key}' on service '{service}'.",
                    series=[],
                )
                continue

            anomaly, dev_pct, strength = self.analyze_metric_deviation(b_val, i_val, key)
            if anomaly:
                anomalies_count += 1
            if correlation_rank.get(strength, 0) > max_rank:
                max_rank = correlation_rank[strength]

            samples[key] = PrometheusMetricSample(
                metric_name=key,
                query=active_q,
                unit=unit,
                baseline_value=round(b_val, 2) if b_val is not None else None,
                observed_value=round(i_val, 2) if i_val is not None else None,
                deviation_pct=dev_pct,
                anomaly_detected=anomaly,
                correlation_strength=strength,  # type: ignore
                status="AVAILABLE",
                message=None,
                series=series_pts[:40],
            )

        highest_strength = [k for k, v in correlation_rank.items() if v == max_rank][0]
        status = "CONNECTED" if any(s.status == "AVAILABLE" for s in samples.values()) else "NO_METRICS_FOUND"

        # Build informative factual summary
        if anomalies_count > 0:
            deviant_names = [s.metric_name for s in samples.values() if s.anomaly_detected]
            summary = (
                f"Prometheus detected {anomalies_count} anomalous metric deviation(s) "
                f"({', '.join(deviant_names)}) for '{service}' during the incident window "
                f"with {highest_strength.lower()} operational correlation."
            )
        elif status == "CONNECTED":
            summary = f"Prometheus connected. Metric telemetry across {len(samples)} indicators is within baseline variance."
        else:
            summary = f"Prometheus connected at {self.base_url}, but no metric series matched service '{service}'."

        return PrometheusEvidence(
            status=status,
            url=self.base_url,
            service=service,
            time_window=tw,
            cpu_utilization=samples.get("cpu_utilization"),
            memory_utilization=samples.get("memory_utilization"),
            request_rate=samples.get("request_rate"),
            error_rate=samples.get("error_rate"),
            p95_latency=samples.get("p95_latency"),
            availability=samples.get("availability"),
            metrics=samples,
            anomalies_detected=anomalies_count,
            highest_correlation=highest_strength,  # type: ignore
            summary=summary,
        )
