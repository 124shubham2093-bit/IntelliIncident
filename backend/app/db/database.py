import sqlite3
import os
from backend.app.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        service TEXT NOT NULL,
        severity TEXT NOT NULL,
        risk TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        anomaly_detected INTEGER NOT NULL,
        anomaly_score REAL NOT NULL,
        status TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        summary TEXT NOT NULL,
        affected_users_count INTEGER NOT NULL,
        root_cause_category TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incident_metrics (
        incident_id TEXT PRIMARY KEY,
        service TEXT NOT NULL,
        affected_users INTEGER NOT NULL,
        error_rate REAL NOT NULL,
        latency_p99 REAL NOT NULL,
        latency_p50 REAL NOT NULL,
        request_volume INTEGER NOT NULL,
        deployment_recency_minutes INTEGER NOT NULL,
        cpu_utilization REAL NOT NULL,
        memory_utilization REAL NOT NULL,
        service_criticality INTEGER NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deployments (
        id TEXT PRIMARY KEY,
        service TEXT NOT NULL,
        commit_hash TEXT NOT NULL,
        deployed_at TEXT NOT NULL,
        environment TEXT NOT NULL,
        status TEXT NOT NULL,
        author TEXT NOT NULL,
        changelog TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runtime_logs (
        id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        log_level TEXT NOT NULL,
        message TEXT NOT NULL,
        stack_trace TEXT,
        FOREIGN KEY (incident_id) REFERENCES incidents (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        customer_tier TEXT NOT NULL,
        subject TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_events (
        id TEXT PRIMARY KEY,
        incident_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        service TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL,
        FOREIGN KEY (incident_id) REFERENCES incidents (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        description TEXT,
        language TEXT NOT NULL,
        framework TEXT,
        repo_owner TEXT,
        repo_name TEXT,
        default_branch TEXT NOT NULL DEFAULT 'main',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS environments (
        id TEXT PRIMARY KEY,
        application_id TEXT NOT NULL,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        api_key TEXT UNIQUE NOT NULL,
        endpoint_url TEXT,
        current_commit TEXT,
        is_production INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (application_id) REFERENCES applications (id)
    );
    """)

    # Safely migrate incidents table with topology foreign references if not present
    cursor.execute("PRAGMA table_info(incidents);")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    if "project_id" not in existing_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN project_id TEXT;")
    if "application_id" not in existing_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN application_id TEXT;")
    if "environment_id" not in existing_cols:
        cursor.execute("ALTER TABLE incidents ADD COLUMN environment_id TEXT;")

    conn.commit()
    conn.close()
