# Prometheus Metric Telemetry Integration

IntelliIncident integrates with **Prometheus** to provide real-time and incident-scoped metric telemetry as a first-class evidence source. Metric telemetry correlates alongside **GitHub** code intelligence and **Sentry** runtime error intelligence to produce explainable, multi-dimensional Root Cause Analysis (RCA).

---

## 1. Architectural Overview

```
                      ┌────────────────────────────────────────┐
                      │          Deployed Application          │
                      └──────────────────┬─────────────────────┘
                                         │ Telemetry / Scrape
                                         ▼
   ┌───────────────────────────────────────────────────────────┐
   │                     Prometheus Server                     │
   │           (e.g., http://localhost:9090)                  │
   └─────────────────────────────┬─────────────────────────────┘
                                 │ HTTP API (v1)
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   IntelliIncident Backend                              │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                     PrometheusService                          │   │
│   │  • Health & Reachability checks (`/-/healthy`, `buildinfo`)    │   │
│   │  • Parameterized PromQL query execution (`query`, `query_range`)│   │
│   │  • Time-window derivation (Baseline vs Incident)               │   │
│   │  • Statistical deviation & anomaly detection                   │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │ PrometheusEvidence                │
│                                    ▼                                   │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    EvidenceCorrelator                          │   │
│   │  • INFRASTRUCTURE: CPU & Memory anomalies                      │   │
│   │  • CODE_ERROR: Error rate surge & Availability drop            │   │
│   │  • DATABASE & NETWORK: P95 Latency spikes                      │   │
│   │  • TRAFFIC: Request rate surges                                │   │
│   │  • Tri-Source Cross-Correlation: GitHub + Sentry + Prometheus  │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │ Root Cause Candidates             │
│                                    ▼                                   │
│                        FastAPI REST API Routes                         │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ JSON API
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   IntelliIncident React Dashboard                      │
│                                                                        │
│   • `PrometheusEvidenceCard.tsx` in Incident Details & Investigation   │
│   • Baseline vs Observed numeric comparisons and deviation badges     │
│   • PromQL query transparency and cross-source correlation tags       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Configuration

Prometheus connectivity is configured via environment variables and defined in `backend/app/core/config.py`:

| Environment Variable | Default Value | Description |
|----------------------|---------------|-------------|
| `PROMETHEUS_URL`     | `http://localhost:9090` | Base URL of the Prometheus server HTTP API |

### Example Configuration (`backend/.env`)
```bash
# Prometheus Metric Telemetry Integration
PROMETHEUS_URL=http://localhost:9090
```

If `PROMETHEUS_URL` is empty, unconfigured, or unreachable, IntelliIncident gracefully degrades:
- The system continues operating without crashing.
- Endpoints return `status: "UNAVAILABLE"` or `"NOT_CONFIGURED"`.
- RCA runs using available telemetry (GitHub, Sentry, runtime logs, database metrics).

---

## 3. Parameterized PromQL Queries

`PrometheusService` executes standardized PromQL queries parameterized by target `{service}`:

| Metric | Primary PromQL Query | Fallback Query | Unit |
|---|---|---|---|
| **CPU Utilization** | `sum(rate(container_cpu_usage_seconds_total{container="{service}"}[5m])) * 100` | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | `%` |
| **Memory Utilization** | `(sum(container_memory_working_set_bytes{container="{service}"}) / sum(container_spec_memory_limit_bytes{container="{service}"})) * 100` | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` | `%` |
| **Request Rate** | `sum(rate(http_requests_total{service="{service}"}[5m]))` | `sum(rate(http_requests_total[5m]))` | `req/s` |
| **Error Rate** | `(sum(rate(http_requests_total{service="{service}",status=~"5.."}[5m])) / clamp_min(sum(rate(http_requests_total{service="{service}"}[5m])), 0.001)) * 100` | `(sum(rate(http_requests_total{status=~"5.."}[5m])) / clamp_min(sum(rate(http_requests_total[5m])), 0.001)) * 100` | `%` |
| **P95 Latency** | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{service="{service}"}[5m])) by (le)) * 1000` | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000` | `ms` |
| **Availability** | `avg_over_time(up{job="{service}"}[5m]) * 100` | `avg_over_time(up[5m]) * 100` | `%` |

---

## 4. Time-Window Derivation & Statistical Deviation

When evaluating an incident at timestamp T:
1. **Pre-Incident Baseline Window**: [T - 60m, T - 15m] (45 minutes of normal historical telemetry).
2. **Incident Window**: [T - 15m, T + 30m] (45 minutes covering deployment recency, onset, and peak impact).

### Deviation Calculation
For each metric, the baseline average is compared to the incident window observed value:
- An anomaly is detected when deviation >= +20% (or availability drops below 95%).
- Correlation strength is categorized as:
  - **HIGH**: deviation >= +50% (or availability drop > 20%)
  - **MEDIUM**: +20% <= deviation < +50%
  - **LOW**: +10% <= deviation < +20%
  - **NONE**: deviation < 10%

---

## 5. Tri-Source Evidence Correlation

IntelliIncident correlates evidence across three independent dimensions:
1. **GitHub Code Intelligence**: Identifies recent deployment commits, changed files, author, and code diffs.
2. **Sentry Runtime Intelligence**: Captures stack traces, exception types, culprits, and unhandled errors.
3. **Prometheus Telemetry**: Quantifies resource saturation (CPU/memory), error rates, and latency shifts.

When all three sources align on an incident:
- `DEPLOYMENT` and `CODE_ERROR` root causes receive verified tri-source cross-correlation evidence.
- Explanations explicitly cite the deployment commit SHA, the Sentry exception type, and the Prometheus metric deviation.

---

## 6. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/prometheus/health` | Returns Prometheus connectivity status, reachability, and version. |
| `GET` | `/api/prometheus/metrics?service={name}` | Returns instant metric values for operational monitoring. |
| `GET` | `/api/prometheus/evidence/{incident_id}` | Returns normalized, correlated Prometheus evidence for a specific incident. |

---

## 7. Frontend User Interface

- **`PrometheusEvidenceCard`**: Renders on the Incident Details and Investigation pages.
- Displays connection status badge, anomalies detected, peak correlation level, and Prometheus server endpoint.
- Visualizes baseline vs observed values, percentage deviations, and expandable PromQL queries for complete diagnostic transparency.
