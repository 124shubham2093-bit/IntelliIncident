import os
import sys

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
from backend.app.core.config import settings
from backend.app.db.database import get_db_connection, init_db

def seed_database():
    data_dir = settings.DATA_DIR
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM evidence_events")
    cursor.execute("DELETE FROM support_tickets")
    cursor.execute("DELETE FROM runtime_logs")
    cursor.execute("DELETE FROM deployments")
    cursor.execute("DELETE FROM incident_metrics")
    cursor.execute("DELETE FROM incidents")
    conn.commit()

    # Load Incidents
    incidents_path = os.path.join(data_dir, "incidents.csv")
    if os.path.exists(incidents_path):
        df_incidents = pd.read_csv(incidents_path)
        for _, row in df_incidents.iterrows():
            cursor.execute("""
            INSERT INTO incidents (
                id, title, service, severity, risk, risk_score,
                anomaly_detected, anomaly_score, status, timestamp,
                summary, affected_users_count, root_cause_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["id"]),
                str(row["title"]),
                str(row["service"]),
                str(row["severity"]),
                str(row["risk"]),
                int(row["risk_score"]),
                int(row["anomaly_detected"]),
                float(row["anomaly_score"]),
                str(row["status"]),
                str(row["timestamp"]),
                str(row["summary"]),
                int(row["affected_users_count"]),
                str(row["root_cause_category"]),
            ))
        print(f"Seeded {len(df_incidents)} incidents.")

    # Load Metrics
    metrics_path = os.path.join(data_dir, "monitoring_metrics.csv")
    if os.path.exists(metrics_path):
        df_metrics = pd.read_csv(metrics_path)
        for _, row in df_metrics.iterrows():
            cursor.execute("""
            INSERT INTO incident_metrics (
                incident_id, service, affected_users, error_rate,
                latency_p99, latency_p50, request_volume,
                deployment_recency_minutes, cpu_utilization,
                memory_utilization, service_criticality
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["incident_id"]),
                str(row["service"]),
                int(row["affected_users"]),
                float(row["error_rate"]),
                float(row["latency_p99"]),
                float(row["latency_p50"]),
                int(row["request_volume"]),
                int(row["deployment_recency_minutes"]),
                float(row["cpu_utilization"]),
                float(row["memory_utilization"]),
                int(row["service_criticality"]),
            ))
        print(f"Seeded {len(df_metrics)} metric records.")

    # Load Deployments
    deployments_path = os.path.join(data_dir, "deployments.csv")
    if os.path.exists(deployments_path):
        df_deployments = pd.read_csv(deployments_path)
        for _, row in df_deployments.iterrows():
            cursor.execute("""
            INSERT INTO deployments (
                id, service, commit_hash, deployed_at, environment,
                status, author, changelog
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["id"]),
                str(row["service"]),
                str(row["commit_hash"]),
                str(row["deployed_at"]),
                str(row["environment"]),
                str(row["status"]),
                str(row["author"]),
                str(row["changelog"]),
            ))
        print(f"Seeded {len(df_deployments)} deployment events.")

    # Load Logs
    logs_path = os.path.join(data_dir, "runtime_logs.csv")
    if os.path.exists(logs_path):
        df_logs = pd.read_csv(logs_path)
        for _, row in df_logs.iterrows():
            cursor.execute("""
            INSERT INTO runtime_logs (
                id, incident_id, timestamp, log_level, message, stack_trace
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(row["id"]),
                str(row["incident_id"]),
                str(row["timestamp"]),
                str(row["log_level"]),
                str(row["message"]),
                str(row.get("stack_trace", "")),
            ))
        print(f"Seeded {len(df_logs)} runtime logs.")

    # Load Tickets
    tickets_path = os.path.join(data_dir, "support_tickets.csv")
    if os.path.exists(tickets_path):
        df_tickets = pd.read_csv(tickets_path)
        for _, row in df_tickets.iterrows():
            cursor.execute("""
            INSERT INTO support_tickets (
                id, incident_id, created_at, customer_tier, subject, sentiment
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(row["id"]),
                str(row["incident_id"]),
                str(row["created_at"]),
                str(row["customer_tier"]),
                str(row["subject"]),
                str(row["sentiment"]),
            ))
        print(f"Seeded {len(df_tickets)} support tickets.")

    # Load Evidence Events
    evidence_path = os.path.join(data_dir, "evidence_events.csv")
    if os.path.exists(evidence_path):
        df_evidence = pd.read_csv(evidence_path)
        for _, row in df_evidence.iterrows():
            cursor.execute("""
            INSERT INTO evidence_events (
                id, incident_id, timestamp, event_type, service, description, severity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["id"]),
                str(row["incident_id"]),
                str(row["timestamp"]),
                str(row["event_type"]),
                str(row["service"]),
                str(row["description"]),
                str(row["severity"]),
            ))
        print(f"Seeded {len(df_evidence)} evidence events.")

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
