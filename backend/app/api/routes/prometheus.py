"""
Prometheus Metrics Intelligence API Routes for IntelliIncident.
Exposes endpoints for verifying Prometheus connectivity, querying real-time
operational metrics, and retrieving incident-scoped Prometheus evidence.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.core.config import settings
from backend.app.schemas.prometheus import (
    PrometheusStatusResponse,
    PrometheusEvidence,
    PrometheusMetricSample,
)
from backend.app.services.prometheus_service import PrometheusService
from backend.app.db.database import get_db_connection

router = APIRouter(prefix="/prometheus", tags=["Prometheus"])
prometheus_service = PrometheusService()


@router.get("/health", response_model=PrometheusStatusResponse)
async def get_prometheus_health():
    """
    Check connectivity, API reachability, and version information of Prometheus.
    Safe endpoint that never crashes even if Prometheus is offline.
    """
    return await prometheus_service.get_health()


@router.get("/metrics", response_model=Dict[str, Optional[float]])
async def get_operational_metrics(service: str = Query("all", description="Target service name or 'all'")):
    """
    Retrieve real-time instant values for operational metrics (CPU, Memory, Request Rate, Error Rate, P95, Availability).
    Returns None for any metric that cannot be queried or is unavailable.
    """
    results: Dict[str, Optional[float]] = {}
    target = "" if service == "all" else service
    for key, conf in prometheus_service.queries.items():
        q = conf["primary"].replace("{service}", target)
        val = await prometheus_service.query_instant(q)
        if val is None and conf.get("fallback"):
            fallback_q = conf["fallback"].replace("{service}", target)
            val = await prometheus_service.query_instant(fallback_q)
        results[key] = round(val, 2) if val is not None else None
    return results


@router.get("/evidence/{incident_id}", response_model=PrometheusEvidence)
async def get_incident_prometheus_evidence(incident_id: str):
    """
    Retrieve normalized Prometheus metric evidence correlated with the incident's service and time window.
    Gracefully handles unconfigured/unreachable Prometheus without failing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, service, timestamp FROM incidents WHERE id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )

    service_name = row["service"]
    incident_ts = row["timestamp"]

    return await prometheus_service.get_incident_metric_evidence(
        service=service_name,
        incident_timestamp=incident_ts,
    )
