"""
PaymentGateway Monitored Microservice Telemetry Producer for IntelliIncident.
Runs as a standalone, independent HTTP service on http://localhost:8001.

Features:
- Genuine business endpoint: POST /api/charge
- Health endpoint: GET /healthz
- Fault injection endpoints: POST /fault/trigger and POST /fault/reset
- Prometheus scrape endpoint: GET /metrics (using official prometheus_client)
- Automatically tracks real HTTP requests, status codes, and latency histograms.
"""

import time
import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel
import uvicorn
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# Initialize dedicated Prometheus registry for PaymentGateway service
registry = CollectorRegistry()

# 1. Real HTTP request counter
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the service.",
    ["service", "method", "endpoint", "status"],
    registry=registry,
)

# 2. Real HTTP request duration histogram (seconds)
# Bucket boundaries configured to capture both normal (<100ms) and degraded (>500ms) requests
LATENCY_BUCKETS = (
    0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["service", "method", "endpoint"],
    buckets=LATENCY_BUCKETS,
    registry=registry,
)

app = FastAPI(
    title="PaymentGateway Microservice",
    description="Simulated production microservice emitting genuine Prometheus metrics for IntelliIncident.",
    version="1.0.0",
)

# Controlled fault injection state (reversible)
fault_state = {
    "active": False,
    "latency_seconds": 0.85,  # 850ms latency surge
    "failure_message": "Database connection pool timeout acquiring JDBC connection (HikariPool-1)",
    "triggered_at": None,
}


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Exclude /metrics from being tracked to prevent scrape noise
    path = request.url.path
    if path == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        duration = time.perf_counter() - start_time
        # Record actual latency in Prometheus histogram
        HTTP_REQUEST_DURATION_SECONDS.labels(
            service="PaymentGateway",
            method=request.method,
            endpoint=path,
        ).observe(duration)

        # Record actual response status in Prometheus request counter
        HTTP_REQUESTS_TOTAL.labels(
            service="PaymentGateway",
            method=request.method,
            endpoint=path,
            status=str(status_code),
        ).inc()


class ChargeRequest(BaseModel):
    amount: float = 99.95
    currency: str = "USD"
    customer_id: str = "cust_corp_882"
    merchant_id: str = "merch_cloud_401"


class FaultTriggerRequest(BaseModel):
    active: bool = True
    latency_seconds: Optional[float] = 0.85
    message: Optional[str] = None


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "PaymentGateway",
        "fault_active": fault_state["active"],
        "timestamp": time.time(),
    }


@app.post("/api/charge")
async def process_charge(payload: ChargeRequest = ChargeRequest()):
    """
    Core business endpoint: simulates charging a payment method.
    When fault_state is active, simulates severe database pool exhaustion:
    incurs 850ms delay and returns HTTP 500 error.
    """
    if fault_state["active"]:
        # Simulate contention and acquire timeout
        await asyncio.sleep(fault_state["latency_seconds"])
        return Response(
            content=(
                f'{{"error": "{fault_state["failure_message"]}", '
                f'"status": "FAILED", "code": "DB_CONNECTION_TIMEOUT"}}'
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )

    # Normal healthy processing: nominal latency (~35ms)
    await asyncio.sleep(0.035)
    return {
        "status": "SUCCESS",
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "amount": payload.amount,
        "currency": payload.currency,
        "processed_at": time.time(),
    }


@app.post("/fault/trigger")
async def trigger_fault(req: FaultTriggerRequest = FaultTriggerRequest()):
    """
    Activate controlled, reversible operational fault mode.
    Simulates database pool acquisition failure on /api/charge.
    """
    fault_state["active"] = req.active
    if req.latency_seconds is not None:
        fault_state["latency_seconds"] = max(0.0, req.latency_seconds)
    if req.message:
        fault_state["failure_message"] = req.message
    fault_state["triggered_at"] = time.time() if req.active else None

    state_desc = "ACTIVATED" if req.active else "RESOLVED"
    return {
        "status": "ok",
        "fault_active": fault_state["active"],
        "latency_seconds": fault_state["latency_seconds"],
        "message": f"Operational fault mode {state_desc}. /api/charge will {'fail with HTTP 500 and elevated latency' if req.active else 'process normally with HTTP 200'}.",
    }


@app.post("/fault/reset")
async def reset_fault():
    """Reset fault mode to normal healthy operation."""
    fault_state["active"] = False
    fault_state["triggered_at"] = None
    return {
        "status": "ok",
        "fault_active": False,
        "message": "Fault mode cleared. PaymentGateway returned to healthy baseline.",
    }


@app.get("/metrics")
async def get_prometheus_metrics():
    """Official Prometheus scrape endpoint."""
    output = generate_latest(registry)
    return Response(content=output, media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
