"""
IntelliIncident Synthetic Dataset Generator
Generates realistic, noisy incident records and operational telemetry data
with stochastic variation, overlapping distributions, and multi-service topology.

Seed: 42 (Deterministic reproducibility)
Target Size: ~850 Incidents with associated telemetry, deployments, logs, and tickets.
"""

import os
import random
import datetime
import pandas as pd
import numpy as np

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

SERVICES_CATALOG = [
    {"service": "payment-gateway", "tier": "Tier 1", "criticality": 5, "base_req": 4500, "base_p50": 45, "base_p99": 180},
    {"service": "auth-service", "tier": "Tier 1", "criticality": 5, "base_req": 7200, "base_p50": 30, "base_p99": 140},
    {"service": "checkout-service", "tier": "Tier 1", "criticality": 4, "base_req": 3800, "base_p50": 60, "base_p99": 240},
    {"service": "order-processing", "tier": "Tier 1", "criticality": 4, "base_req": 2900, "base_p50": 85, "base_p99": 320},
    {"service": "inventory-api", "tier": "Tier 2", "criticality": 3, "base_req": 2100, "base_p50": 40, "base_p99": 190},
    {"service": "user-profile", "tier": "Tier 2", "criticality": 3, "base_req": 3100, "base_p50": 35, "base_p99": 160},
    {"service": "search-indexer", "tier": "Tier 2", "criticality": 2, "base_req": 1400, "base_p50": 110, "base_p99": 450},
    {"service": "notification-worker", "tier": "Tier 3", "criticality": 2, "base_req": 950, "base_p50": 70, "base_p99": 280},
]

ROOT_CAUSE_CATEGORIES = [
    "DEPLOYMENT",
    "DATABASE",
    "INFRASTRUCTURE",
    "CODE_ERROR",
    "TRAFFIC",
    "NETWORK",
]

INCIDENT_TITLES = {
    "DEPLOYMENT": [
        "Null pointer exception in payload serialization post-release",
        "Config flag default inversion causing request rejections",
        "Dependency version mismatch in gRPC protobuf schema",
        "Stale cache invalidation logic deployed in Canary",
        "Database migration lock timeout during schema rollout",
    ],
    "DATABASE": [
        "Connection pool saturation under sustained transaction load",
        "Unindexed query scan causing read replica CPU spike",
        "Deadlock cycle in distributed checkout table lock",
        "Redis cluster shard memory limit eviction cascade",
        "Slow query cascade triggering client connection timeout",
    ],
    "INFRASTRUCTURE": [
        "Pod memory limit hit triggering repeated OOMKilled events",
        "High CPU throttling on Kubernetes node worker pool",
        "Ephemeral disk volume full due to unrotated application logs",
        "Garbage collection pause duration exceeding 1500ms",
        "File descriptor limit reached on upstream reverse proxy",
    ],
    "CODE_ERROR": [
        "Unhandled arithmetic overflow in currency conversion",
        "Recursive call in JSON parsing leading to stack exhaustion",
        "Race condition in concurrent token refresh logic",
        "Corrupted response payload format failing client validation",
        "Memory leak in unclosed HTTP response stream handler",
    ],
    "TRAFFIC": [
        "Sudden traffic surge exceeding rate limiter bucket capacity",
        "Flash sale burst traffic causing ingress queue build-up",
        "Distributed crawler burst triggering endpoint 429 retries",
        "Batch data import job executed during peak consumer hours",
        "Spike in unauthenticated request probe flood",
    ],
    "NETWORK": [
        "DNS resolution timeouts between VPC private subnets",
        "TCP socket connection reset by peer on egress gateway",
        "Inter-region transit latency degradation exceeding SLA",
        "TLS certificate handshake timeout on third-party webhook",
        "Network packet loss on Kubernetes overlay CNI bridge",
    ],
}

def generate_dataset(num_records=850):
    incidents = []
    metrics = []
    deployments = []
    logs = []
    tickets = []
    evidence_events = []

    now = datetime.datetime(2026, 9, 26, 12, 0, 0)

    # Pre-generate 120 deployment records
    for dep_idx in range(120):
        svc_info = random.choice(SERVICES_CATALOG)
        dep_time = now - datetime.timedelta(minutes=random.randint(5, 43200))
        commit_hash = f"{random.randint(0x1000000, 0xfffffff):07x}"
        author = random.choice(["alex.chen", "sarah.k", "marcus.v", "priya.n", "jordan.b", "elena.r"])
        dep_status = random.choices(["SUCCESS", "FAILED", "ROLLED_BACK"], weights=[0.82, 0.10, 0.08])[0]
        deployments.append({
            "id": f"DEP-{1000 + dep_idx}",
            "service": svc_info["service"],
            "commit_hash": commit_hash,
            "deployed_at": dep_time.isoformat() + "Z",
            "environment": "production",
            "status": dep_status,
            "author": author,
            "changelog": f"Release v2.{random.randint(1, 28)}.{random.randint(0, 9)} - updates for {svc_info['service']}",
        })

    # Realistic noisy distribution for Severity:
    # LOW (~36%), MEDIUM (~34%), HIGH (~20%), CRITICAL (~10%)
    severity_weights = [0.36, 0.34, 0.20, 0.10]
    severity_choices = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    for idx in range(num_records):
        inc_id = f"INC-{8000 + idx}"
        svc = random.choice(SERVICES_CATALOG)
        service_name = svc["service"]
        service_tier = svc["tier"]
        criticality = svc["criticality"]

        # Base severity choice with noise
        severity = random.choices(severity_choices, weights=severity_weights)[0]

        # Primary root cause category
        category = random.choice(ROOT_CAUSE_CATEGORIES)
        title = random.choice(INCIDENT_TITLES[category])

        # Generate realistic noisy telemetry features with overlapping distributions
        # We explicitly add noise so no single trivial if/else separates the classes.

        if severity == "LOW":
            # Typically modest, but with outliers
            error_rate = np.clip(np.random.normal(loc=1.8, scale=1.5), 0.05, 12.0)
            latency_p50 = np.clip(np.random.normal(loc=svc["base_p50"] * 1.05, scale=15), 10, 300)
            latency_p99 = np.clip(np.random.normal(loc=svc["base_p99"] * 1.15, scale=50), 40, 850)
            cpu = np.clip(np.random.normal(loc=35, scale=14), 10, 82)
            mem = np.clip(np.random.normal(loc=42, scale=12), 15, 80)
            affected_users = int(np.clip(np.random.exponential(scale=60), 0, 800))
            deployment_recency = int(np.clip(np.random.exponential(scale=180), 5, 720))
            req_vol = int(np.clip(np.random.normal(loc=svc["base_req"], scale=600), 200, 10000))
            risk_score = int(np.clip(np.random.normal(loc=22, scale=10), 5, 45))
            anomaly_detected = random.random() < 0.18 # Some low incidents trigger anomaly false positives
            anomaly_score = float(np.clip(np.random.normal(loc=0.35, scale=0.25), -0.3, 0.75))

        elif severity == "MEDIUM":
            error_rate = np.clip(np.random.normal(loc=6.5, scale=3.2), 0.5, 24.0)
            latency_p50 = np.clip(np.random.normal(loc=svc["base_p50"] * 1.35, scale=35), 20, 500)
            latency_p99 = np.clip(np.random.normal(loc=svc["base_p99"] * 1.6, scale=180), 80, 1600)
            cpu = np.clip(np.random.normal(loc=62, scale=16), 20, 92)
            mem = np.clip(np.random.normal(loc=66, scale=14), 25, 90)
            affected_users = int(np.clip(np.random.exponential(scale=450), 10, 3500))
            deployment_recency = int(np.clip(np.random.exponential(scale=120), 3, 480))
            req_vol = int(np.clip(np.random.normal(loc=svc["base_req"] * 1.15, scale=900), 300, 12000))
            risk_score = int(np.clip(np.random.normal(loc=48, scale=11), 26, 72))
            anomaly_detected = random.random() < 0.62
            anomaly_score = float(np.clip(np.random.normal(loc=0.05, scale=0.30), -0.6, 0.5))

        elif severity == "HIGH":
            error_rate = np.clip(np.random.normal(loc=16.0, scale=6.5), 2.5, 38.0)
            latency_p50 = np.clip(np.random.normal(loc=svc["base_p50"] * 2.0, scale=60), 40, 800)
            latency_p99 = np.clip(np.random.normal(loc=svc["base_p99"] * 2.4, scale=320), 150, 2400)
            cpu = np.clip(np.random.normal(loc=78, scale=12), 35, 98)
            mem = np.clip(np.random.normal(loc=80, scale=11), 40, 96)
            affected_users = int(np.clip(np.random.exponential(scale=2800), 100, 18000))
            deployment_recency = int(np.clip(np.random.exponential(scale=70), 2, 300))
            req_vol = int(np.clip(np.random.normal(loc=svc["base_req"] * 1.35, scale=1200), 500, 14000))
            risk_score = int(np.clip(np.random.normal(loc=72, scale=9), 50, 89))
            anomaly_detected = random.random() < 0.88
            anomaly_score = float(np.clip(np.random.normal(loc=-0.35, scale=0.25), -0.85, 0.2))

        else: # CRITICAL
            error_rate = np.clip(np.random.normal(loc=31.0, scale=9.0), 8.0, 50.0)
            latency_p50 = np.clip(np.random.normal(loc=svc["base_p50"] * 2.8, scale=90), 80, 1200)
            latency_p99 = np.clip(np.random.normal(loc=svc["base_p99"] * 3.5, scale=450), 300, 3500)
            cpu = np.clip(np.random.normal(loc=89, scale=8), 55, 99)
            mem = np.clip(np.random.normal(loc=88, scale=8), 60, 99)
            affected_users = int(np.clip(np.random.exponential(scale=9500), 800, 48000))
            deployment_recency = int(np.clip(np.random.exponential(scale=45), 1, 180))
            req_vol = int(np.clip(np.random.normal(loc=svc["base_req"] * 1.5, scale=1600), 800, 16000))
            risk_score = int(np.clip(np.random.normal(loc=89, scale=6), 74, 99))
            anomaly_detected = random.random() < 0.96
            anomaly_score = float(np.clip(np.random.normal(loc=-0.65, scale=0.18), -0.95, -0.1))

        # Realistically noisy category-specific adjustments:
        # e.g. Deployment incidents often correlate with recent deployment, but not always!
        if category == "DEPLOYMENT":
            if random.random() < 0.72:
                deployment_recency = random.randint(3, 40)
        elif category == "DATABASE":
            if random.random() < 0.75:
                latency_p99 = latency_p99 * random.uniform(1.2, 1.6)
        elif category == "INFRASTRUCTURE":
            if random.random() < 0.70:
                cpu = max(cpu, random.uniform(84, 99))
        elif category == "TRAFFIC":
            if random.random() < 0.75:
                req_vol = int(req_vol * random.uniform(1.4, 2.2))

        # Derive Risk linguistic label
        if risk_score >= 82:
            risk_label = "CRITICAL"
        elif risk_score >= 65:
            risk_label = "HIGH"
        elif risk_score >= 40:
            risk_label = "MEDIUM"
        else:
            risk_label = "LOW"

        # Timestamp in past 45 days
        minutes_ago = random.randint(15, 64800)
        inc_time = now - datetime.timedelta(minutes=minutes_ago)

        status_choices = ["OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED"]
        if minutes_ago < 180:
            status = random.choices(status_choices, weights=[0.45, 0.40, 0.12, 0.03])[0]
        elif minutes_ago < 1440:
            status = random.choices(status_choices, weights=[0.10, 0.30, 0.40, 0.20])[0]
        else:
            status = random.choices(status_choices, weights=[0.02, 0.05, 0.15, 0.78])[0]

        summary = (
            f"Degradation on {service_name} ({service_tier}): observed {error_rate:.1f}% error rate "
            f"and P99 latency of {latency_p99:.0f}ms impacting an estimated {affected_users:,} active users. "
            f"Primary symptom matches {category.lower()} pattern."
        )

        incidents.append({
            "id": inc_id,
            "title": f"{title} on {service_name}",
            "service": service_name,
            "severity": severity,
            "risk": risk_label,
            "risk_score": risk_score,
            "anomaly_detected": 1 if anomaly_detected else 0,
            "anomaly_score": round(anomaly_score, 4),
            "status": status,
            "timestamp": inc_time.isoformat() + "Z",
            "summary": summary,
            "affected_users_count": affected_users,
            "root_cause_category": category,
        })

        metrics.append({
            "incident_id": inc_id,
            "service": service_name,
            "affected_users": affected_users,
            "error_rate": round(float(error_rate), 2),
            "latency_p99": round(float(latency_p99), 1),
            "latency_p50": round(float(latency_p50), 1),
            "request_volume": req_vol,
            "deployment_recency_minutes": deployment_recency,
            "cpu_utilization": round(float(cpu), 1),
            "memory_utilization": round(float(mem), 1),
            "service_criticality": criticality,
        })

        # Generate 2-4 runtime diagnostic logs per incident
        log_levels = ["ERROR", "WARN", "INFO"]
        for l_idx in range(random.randint(2, 4)):
            log_time = inc_time + datetime.timedelta(seconds=random.randint(5, 120))
            logs.append({
                "id": f"LOG-{inc_id}-{l_idx+1}",
                "incident_id": inc_id,
                "timestamp": log_time.isoformat() + "Z",
                "log_level": random.choice(log_levels) if severity != "CRITICAL" else "ERROR",
                "message": f"[{service_name}] Execution exception during request dispatch: {title}",
                "stack_trace": f"Traceback (most recent call last):\n  File \"app/handlers/dispatch.py\", line 142, in process\n  ServiceError: {title}",
            })

        # Generate 1-3 customer support tickets
        if affected_users > 50:
            for t_idx in range(random.randint(1, 3)):
                tick_time = inc_time + datetime.timedelta(minutes=random.randint(2, 25))
                tickets.append({
                    "id": f"TCK-{inc_id}-{t_idx+1}",
                    "incident_id": inc_id,
                    "created_at": tick_time.isoformat() + "Z",
                    "customer_tier": random.choice(["Enterprise", "Business", "Free"]),
                    "subject": f"Failures encountered on {service_name}: {title}",
                    "sentiment": "NEGATIVE" if severity in ["HIGH", "CRITICAL"] else "NEUTRAL",
                })

        # Evidence events (chronological timeline)
        event_types = ["MONITORING_ALERT", "ERROR_SPIKE", "LATENCY_INCREASE"]
        if deployment_recency <= 60:
            event_types.insert(0, "DEPLOYMENT")
        if req_vol > svc["base_req"] * 1.3:
            event_types.append("TRAFFIC_SURGE")

        for e_idx, ev_type in enumerate(event_types):
            ev_time = inc_time - datetime.timedelta(minutes=random.randint(1, 15) * (len(event_types) - e_idx))
            evidence_events.append({
                "id": f"EVT-{inc_id}-{e_idx+1}",
                "incident_id": inc_id,
                "timestamp": ev_time.isoformat() + "Z",
                "event_type": ev_type,
                "service": service_name,
                "description": f"Telemetry signal: {ev_type.replace('_', ' ').title()} recorded on {service_name}",
                "severity": "CRITICAL" if severity == "CRITICAL" else "WARN",
            })

    # Convert to DataFrames and save
    df_incidents = pd.DataFrame(incidents)
    df_metrics = pd.DataFrame(metrics)
    df_deployments = pd.DataFrame(deployments)
    df_logs = pd.DataFrame(logs)
    df_tickets = pd.DataFrame(tickets)
    df_evidence = pd.DataFrame(evidence_events)

    df_incidents.to_csv(os.path.join(OUTPUT_DIR, "incidents.csv"), index=False)
    df_metrics.to_csv(os.path.join(OUTPUT_DIR, "monitoring_metrics.csv"), index=False)
    df_deployments.to_csv(os.path.join(OUTPUT_DIR, "deployments.csv"), index=False)
    df_logs.to_csv(os.path.join(OUTPUT_DIR, "runtime_logs.csv"), index=False)
    df_tickets.to_csv(os.path.join(OUTPUT_DIR, "support_tickets.csv"), index=False)
    df_evidence.to_csv(os.path.join(OUTPUT_DIR, "evidence_events.csv"), index=False)

    print(f"Generated {len(df_incidents)} incidents successfully.")
    print("Severity distribution:")
    print(df_incidents["severity"].value_counts())
    print("Root cause distribution:")
    print(df_incidents["root_cause_category"].value_counts())
    print(f"Data saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_dataset()
