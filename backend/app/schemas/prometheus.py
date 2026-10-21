"""
Prometheus Metric Telemetry Schemas for IntelliIncident.
Defines normalized Pydantic models for Prometheus connection status, metric samples,
baseline time windows, statistical deviation analysis, and RCA evidence correlation.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class PrometheusStatusResponse(BaseModel):
    """Normalized health and reachability response for Prometheus."""
    status: Literal["CONNECTED", "NOT_CONFIGURED", "UNAVAILABLE", "ERROR"]
    url: str
    reachable: bool
    version: Optional[str] = None
    message: str


class PrometheusSeriesPoint(BaseModel):
    """Single time-series point (timestamp in unix seconds, value)."""
    timestamp: float
    value: float


class PrometheusTimeWindow(BaseModel):
    """Time-window derivation around an incident for baseline vs incident comparison."""
    incident_time: str
    baseline_start: str
    baseline_end: str
    incident_start: str
    incident_end: str


class PrometheusMetricSample(BaseModel):
    """Normalized metric evaluation comparing pre-incident baseline to incident-window value."""
    metric_name: str
    query: str
    unit: str
    baseline_value: Optional[float] = None
    observed_value: Optional[float] = None
    deviation_pct: Optional[float] = None
    anomaly_detected: bool = False
    correlation_strength: Literal["NONE", "LOW", "MEDIUM", "HIGH"] = "NONE"
    status: Literal["AVAILABLE", "UNAVAILABLE", "NOT_FOUND"] = "AVAILABLE"
    message: Optional[str] = None
    series: List[PrometheusSeriesPoint] = Field(default_factory=list)


class PrometheusEvidence(BaseModel):
    """First-class evidence structure fed into EvidenceCorrelator and RootCauseEngine."""
    status: str  # "CONNECTED", "NOT_CONFIGURED", "UNAVAILABLE", "NO_METRICS_FOUND", "ERROR"
    url: str
    service: Optional[str] = None
    time_window: Optional[PrometheusTimeWindow] = None
    cpu_utilization: Optional[PrometheusMetricSample] = None
    memory_utilization: Optional[PrometheusMetricSample] = None
    request_rate: Optional[PrometheusMetricSample] = None
    error_rate: Optional[PrometheusMetricSample] = None
    p95_latency: Optional[PrometheusMetricSample] = None
    availability: Optional[PrometheusMetricSample] = None
    metrics: Dict[str, PrometheusMetricSample] = Field(default_factory=dict)
    anomalies_detected: int = 0
    highest_correlation: Literal["NONE", "LOW", "MEDIUM", "HIGH"] = "NONE"
    summary: str
