"""
Project, Application, and Environment Management Service.
Handles software hierarchy, cryptographic API key generation, parent-child integrity,
service resolution, and connection guides.
"""

import datetime
import re
import secrets
import uuid
from typing import Dict, Any, List, Optional, Tuple

from backend.app.db.database import get_db_connection
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ApplicationCreate,
    ApplicationUpdate,
    EnvironmentCreate,
    EnvironmentUpdate,
    ConnectionGuideResponse,
)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug or "default"


def _generate_api_key() -> str:
    # Cryptographically secure random token: 32 bytes hex (64 chars)
    random_part = secrets.token_hex(24)
    return f"ii_live_{random_part}"


def _mask_api_key(key: str) -> str:
    if not key:
        return "ii_live_..."
    if len(key) <= 16:
        return f"{key[:8]}...{key[-4:]}"
    return f"{key[:10]}...{key[-6:]}"


class ProjectService:

    # ==========================================
    # Project Operations
    # ==========================================

    def create_project(self, data: ProjectCreate) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        slug = data.slug.strip() if data.slug else _slugify(data.name)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Check slug uniqueness
        cursor.execute("SELECT id FROM projects WHERE slug = ?", (slug,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Project with slug '{slug}' already exists.")

        cursor.execute("""
            INSERT INTO projects (id, name, slug, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, data.name.strip(), slug, data.description, now, now))
        conn.commit()
        conn.close()

        return {
            "id": project_id,
            "name": data.name.strip(),
            "slug": slug,
            "description": data.description,
            "application_count": 0,
            "created_at": now,
            "updated_at": now,
        }

    def get_projects(self) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM applications a WHERE a.project_id = p.id) AS application_count
            FROM projects p
            ORDER BY p.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "slug": r["slug"],
                "description": r["description"],
                "application_count": r["application_count"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM applications a WHERE a.project_id = p.id) AS application_count
            FROM projects p
            WHERE p.id = ?
        """, (project_id,))
        r = cursor.fetchone()
        conn.close()

        if not r:
            return None

        return {
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "description": r["description"],
            "application_count": r["application_count"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def update_project(self, project_id: str, data: ProjectUpdate) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return None

        name = data.name.strip() if data.name is not None else existing["name"]
        slug = data.slug.strip() if data.slug is not None else existing["slug"]
        description = data.description if data.description is not None else existing["description"]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if slug != existing["slug"]:
            cursor.execute("SELECT id FROM projects WHERE slug = ? AND id != ?", (slug, project_id))
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"Project with slug '{slug}' already exists.")

        cursor.execute("""
            UPDATE projects
            SET name = ?, slug = ?, description = ?, updated_at = ?
            WHERE id = ?
        """, (name, slug, description, now, project_id))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM applications WHERE project_id = ?", (project_id,))
        app_count = cursor.fetchone()[0]
        conn.close()

        return {
            "id": project_id,
            "name": name,
            "slug": slug,
            "description": description,
            "application_count": app_count,
            "created_at": existing["created_at"],
            "updated_at": now,
        }

    def delete_project(self, project_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            conn.close()
            return False

        # Protect dependent applications
        cursor.execute("SELECT COUNT(*) FROM applications WHERE project_id = ?", (project_id,))
        app_count = cursor.fetchone()[0]
        if app_count > 0:
            conn.close()
            raise ValueError(
                f"Cannot delete project '{project_id}' with {app_count} active application(s). "
                "Delete dependent applications first to preserve system integrity."
            )

        # Protect historical incidents
        cursor.execute("SELECT COUNT(*) FROM incidents WHERE project_id = ?", (project_id,))
        inc_count = cursor.fetchone()[0]
        if inc_count > 0:
            conn.close()
            raise ValueError(
                f"Cannot delete project '{project_id}' because {inc_count} historical incident(s) reference it."
            )

        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        conn.close()
        return True

    # ==========================================
    # Application Operations
    # ==========================================

    def create_application(self, project_id: str, data: ApplicationCreate) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validate parent project
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Parent project '{project_id}' does not exist.")

        app_id = f"app_{uuid.uuid4().hex[:12]}"
        slug = data.slug.strip() if data.slug else _slugify(data.name)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Slug uniqueness per project
        cursor.execute("SELECT id FROM applications WHERE project_id = ? AND slug = ?", (project_id, slug))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Application with slug '{slug}' already exists in this project.")

        cursor.execute("""
            INSERT INTO applications (
                id, project_id, name, slug, description, language, framework,
                repo_owner, repo_name, default_branch, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            project_id,
            data.name.strip(),
            slug,
            data.description,
            data.language.strip().lower(),
            data.framework.strip() if data.framework else None,
            data.repo_owner.strip() if data.repo_owner else None,
            data.repo_name.strip() if data.repo_name else None,
            data.default_branch.strip() if data.default_branch else "main",
            now,
            now,
        ))
        conn.commit()
        conn.close()

        return {
            "id": app_id,
            "project_id": project_id,
            "name": data.name.strip(),
            "slug": slug,
            "description": data.description,
            "language": data.language.strip().lower(),
            "framework": data.framework.strip() if data.framework else None,
            "repo_owner": data.repo_owner.strip() if data.repo_owner else None,
            "repo_name": data.repo_name.strip() if data.repo_name else None,
            "default_branch": data.default_branch.strip() if data.default_branch else "main",
            "environment_count": 0,
            "created_at": now,
            "updated_at": now,
        }

    def get_applications_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.*,
                   (SELECT COUNT(*) FROM environments e WHERE e.application_id = a.id) AS environment_count
            FROM applications a
            WHERE a.project_id = ?
            ORDER BY a.created_at ASC
        """, (project_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": r["id"],
                "project_id": r["project_id"],
                "name": r["name"],
                "slug": r["slug"],
                "description": r["description"],
                "language": r["language"],
                "framework": r["framework"],
                "repo_owner": r["repo_owner"],
                "repo_name": r["repo_name"],
                "default_branch": r["default_branch"],
                "environment_count": r["environment_count"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def get_application_by_id(self, application_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.*,
                   (SELECT COUNT(*) FROM environments e WHERE e.application_id = a.id) AS environment_count
            FROM applications a
            WHERE a.id = ?
        """, (application_id,))
        r = cursor.fetchone()
        conn.close()

        if not r:
            return None

        return {
            "id": r["id"],
            "project_id": r["project_id"],
            "name": r["name"],
            "slug": r["slug"],
            "description": r["description"],
            "language": r["language"],
            "framework": r["framework"],
            "repo_owner": r["repo_owner"],
            "repo_name": r["repo_name"],
            "default_branch": r["default_branch"],
            "environment_count": r["environment_count"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def update_application(self, application_id: str, data: ApplicationUpdate) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return None

        name = data.name.strip() if data.name is not None else existing["name"]
        slug = data.slug.strip() if data.slug is not None else existing["slug"]
        description = data.description if data.description is not None else existing["description"]
        language = data.language.strip().lower() if data.language is not None else existing["language"]
        framework = data.framework.strip() if data.framework is not None else existing["framework"]
        repo_owner = data.repo_owner.strip() if data.repo_owner is not None else existing["repo_owner"]
        repo_name = data.repo_name.strip() if data.repo_name is not None else existing["repo_name"]
        default_branch = data.default_branch.strip() if data.default_branch is not None else existing["default_branch"]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if slug != existing["slug"]:
            cursor.execute(
                "SELECT id FROM applications WHERE project_id = ? AND slug = ? AND id != ?",
                (existing["project_id"], slug, application_id),
            )
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"Application with slug '{slug}' already exists in this project.")

        cursor.execute("""
            UPDATE applications
            SET name = ?, slug = ?, description = ?, language = ?, framework = ?,
                repo_owner = ?, repo_name = ?, default_branch = ?, updated_at = ?
            WHERE id = ?
        """, (
            name, slug, description, language, framework,
            repo_owner, repo_name, default_branch, now, application_id
        ))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM environments WHERE application_id = ?", (application_id,))
        env_count = cursor.fetchone()[0]
        conn.close()

        return {
            "id": application_id,
            "project_id": existing["project_id"],
            "name": name,
            "slug": slug,
            "description": description,
            "language": language,
            "framework": framework,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "default_branch": default_branch,
            "environment_count": env_count,
            "created_at": existing["created_at"],
            "updated_at": now,
        }

    def delete_application(self, application_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM applications WHERE id = ?", (application_id,))
        if not cursor.fetchone():
            conn.close()
            return False

        # Protect dependent environments
        cursor.execute("SELECT COUNT(*) FROM environments WHERE application_id = ?", (application_id,))
        env_count = cursor.fetchone()[0]
        if env_count > 0:
            conn.close()
            raise ValueError(
                f"Cannot delete application '{application_id}' with {env_count} active environment(s). "
                "Delete dependent environments first."
            )

        # Protect historical incidents
        cursor.execute("SELECT COUNT(*) FROM incidents WHERE application_id = ?", (application_id,))
        inc_count = cursor.fetchone()[0]
        if inc_count > 0:
            conn.close()
            raise ValueError(
                f"Cannot delete application '{application_id}' because {inc_count} historical incident(s) reference it."
            )

        cursor.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        conn.commit()
        conn.close()
        return True

    # ==========================================
    # Environment Operations
    # ==========================================

    def create_environment(self, application_id: str, data: EnvironmentCreate) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validate application
        cursor.execute("SELECT id FROM applications WHERE id = ?", (application_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Application '{application_id}' does not exist.")

        env_id = f"env_{uuid.uuid4().hex[:12]}"
        slug = data.slug.strip() if data.slug else _slugify(data.name)
        api_key = _generate_api_key()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        is_prod = 1 if data.is_production else 0

        # Check slug uniqueness within application
        cursor.execute("SELECT id FROM environments WHERE application_id = ? AND slug = ?", (application_id, slug))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Environment with slug '{slug}' already exists for this application.")

        cursor.execute("""
            INSERT INTO environments (
                id, application_id, name, slug, api_key, endpoint_url,
                current_commit, is_production, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            env_id,
            application_id,
            data.name.strip(),
            slug,
            api_key,
            data.endpoint_url.strip() if data.endpoint_url else None,
            data.current_commit.strip() if data.current_commit else None,
            is_prod,
            now,
            now,
        ))
        conn.commit()
        conn.close()

        # Full api_key is returned ONCE upon creation
        return {
            "id": env_id,
            "application_id": application_id,
            "name": data.name.strip(),
            "slug": slug,
            "api_key": api_key,
            "api_key_preview": _mask_api_key(api_key),
            "endpoint_url": data.endpoint_url.strip() if data.endpoint_url else None,
            "current_commit": data.current_commit.strip() if data.current_commit else None,
            "is_production": bool(is_prod),
            "created_at": now,
            "updated_at": now,
        }

    def get_environments_by_application(self, application_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM environments
            WHERE application_id = ?
            ORDER BY is_production DESC, created_at ASC
        """, (application_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": r["id"],
                "application_id": r["application_id"],
                "name": r["name"],
                "slug": r["slug"],
                "api_key": None,  # Masked: never expose full key in listing
                "api_key_preview": _mask_api_key(r["api_key"]),
                "endpoint_url": r["endpoint_url"],
                "current_commit": r["current_commit"],
                "is_production": bool(r["is_production"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def get_environment_by_id(self, environment_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM environments WHERE id = ?", (environment_id,))
        r = cursor.fetchone()
        conn.close()

        if not r:
            return None

        return {
            "id": r["id"],
            "application_id": r["application_id"],
            "name": r["name"],
            "slug": r["slug"],
            "api_key": None,  # Masked
            "api_key_preview": _mask_api_key(r["api_key"]),
            "endpoint_url": r["endpoint_url"],
            "current_commit": r["current_commit"],
            "is_production": bool(r["is_production"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def get_environment_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Look up environment by authenticating its raw API key."""
        if not api_key or not isinstance(api_key, str) or not api_key.startswith("ii_live_"):
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.*, a.project_id, a.slug AS app_slug, a.name AS app_name,
                   a.repo_owner, a.repo_name, a.default_branch,
                   p.name AS project_name, p.slug AS project_slug
            FROM environments e
            JOIN applications a ON a.id = e.application_id
            JOIN projects p ON p.id = a.project_id
            WHERE e.api_key = ?
        """, (api_key.strip(),))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)

    def regenerate_api_key(self, environment_id: str) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM environments WHERE id = ?", (environment_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Environment '{environment_id}' does not exist.")

        new_key = _generate_api_key()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("""
            UPDATE environments
            SET api_key = ?, updated_at = ?
            WHERE id = ?
        """, (new_key, now, environment_id))
        conn.commit()
        conn.close()

        return {
            "id": environment_id,
            "api_key": new_key,
            "api_key_preview": _mask_api_key(new_key),
            "message": "Store this key securely. It will not be fully displayed again.",
        }

    def update_environment(self, environment_id: str, data: EnvironmentUpdate) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM environments WHERE id = ?", (environment_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return None

        name = data.name.strip() if data.name is not None else existing["name"]
        slug = data.slug.strip() if data.slug is not None else existing["slug"]
        endpoint_url = data.endpoint_url.strip() if data.endpoint_url is not None else existing["endpoint_url"]
        current_commit = data.current_commit.strip() if data.current_commit is not None else existing["current_commit"]
        is_prod = (1 if data.is_production else 0) if data.is_production is not None else existing["is_production"]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if slug != existing["slug"]:
            cursor.execute(
                "SELECT id FROM environments WHERE application_id = ? AND slug = ? AND id != ?",
                (existing["application_id"], slug, environment_id),
            )
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"Environment with slug '{slug}' already exists for this application.")

        cursor.execute("""
            UPDATE environments
            SET name = ?, slug = ?, endpoint_url = ?, current_commit = ?,
                is_production = ?, updated_at = ?
            WHERE id = ?
        """, (name, slug, endpoint_url, current_commit, is_prod, now, environment_id))
        conn.commit()
        conn.close()

        return {
            "id": environment_id,
            "application_id": existing["application_id"],
            "name": name,
            "slug": slug,
            "api_key": None,
            "api_key_preview": _mask_api_key(existing["api_key"]),
            "endpoint_url": endpoint_url,
            "current_commit": current_commit,
            "is_production": bool(is_prod),
            "created_at": existing["created_at"],
            "updated_at": now,
        }

    def delete_environment(self, environment_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM environments WHERE id = ?", (environment_id,))
        if not cursor.fetchone():
            conn.close()
            return False

        # Protect historical incidents
        cursor.execute("SELECT COUNT(*) FROM incidents WHERE environment_id = ?", (environment_id,))
        inc_count = cursor.fetchone()[0]
        if inc_count > 0:
            conn.close()
            raise ValueError(
                f"Cannot delete environment '{environment_id}' because {inc_count} historical incident(s) reference it."
            )

        cursor.execute("DELETE FROM environments WHERE id = ?", (environment_id,))
        conn.commit()
        conn.close()
        return True

    # ==========================================
    # Service Resolution Helper
    # ==========================================

    def resolve_service_application(self, service_name_or_slug: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a microservice name or slug string from telemetry/incidents
        to its registered Application and Project entities.
        """
        if not service_name_or_slug or not isinstance(service_name_or_slug, str):
            return None

        clean_name = service_name_or_slug.strip()
        slug = _slugify(clean_name)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.*, p.name AS project_name, p.slug AS project_slug
            FROM applications a
            JOIN projects p ON p.id = a.project_id
            WHERE a.slug = ? OR LOWER(a.name) = LOWER(?)
            LIMIT 1
        """, (slug, clean_name))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)

    # ==========================================
    # Connection Guide
    # ==========================================

    def get_connection_guide(self, environment_id: str, base_url: str = "http://localhost:8000") -> ConnectionGuideResponse:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.*, a.name AS app_name, a.slug AS app_slug,
                   p.id AS proj_id, p.name AS proj_name
            FROM environments e
            JOIN applications a ON a.id = e.application_id
            JOIN projects p ON p.id = a.project_id
            WHERE e.id = ?
        """, (environment_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Environment '{environment_id}' does not exist.")

        key_preview = _mask_api_key(row["api_key"])
        app_slug = row["app_slug"]
        ingest_url = f"{base_url.rstrip('/')}/api/incidents"

        curl_snippet = f"""# Send runtime incident & telemetry from deployed service
curl -X POST "{ingest_url}" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: {key_preview}" \\
  -d '{{
    "title": "Database Connection Pool Exhaustion",
    "service": "{app_slug}",
    "summary": "Sudden surge in pool timeout exceptions following traffic spike",
    "status": "OPEN",
    "affected_users_count": 450,
    "metrics": {{
      "error_rate": 18.5,
      "latency_p99": 1420.0,
      "latency_p50": 110.0,
      "request_volume": 3200,
      "deployment_recency_minutes": 45,
      "cpu_utilization": 82.0,
      "memory_utilization": 88.0,
      "service_criticality": 3
    }},
    "logs": [
      {{
        "log_level": "ERROR",
        "message": "ConnectionTimeout: Timeout acquiring connection from pool after 30000ms",
        "stack_trace": "File \\"app/db/pool.py\\", line 84, in acquire_connection"
      }}
    ],
    "deployments": [
      {{
        "commit_hash": "{row['current_commit'] or 'a1b2c3d'}",
        "environment": "{row['name']}",
        "status": "SUCCESS"
      }}
    ]
  }}'"""

        python_snippet = f"""import requests

INTELLI_ENDPOINT = "{ingest_url}"
INTELLI_API_KEY = "{key_preview}"  # Replace with your full ii_live_... key

payload = {{
    "title": "Payment Microservice Connection Timeout",
    "service": "{app_slug}",
    "status": "OPEN",
    "affected_users_count": 320,
    "metrics": {{
        "error_rate": 22.4,
        "latency_p99": 980.0,
        "deployment_recency_minutes": 30,
        "service_criticality": 3
    }},
    "logs": [
        {{
            "log_level": "ERROR",
            "message": "HTTP 504 Gateway Timeout while calling upstream provider",
            "stack_trace": "File \\"services/payment.py\\", line 124, in process_charge"
        }}
    ],
    "deployments": [
        {{
            "commit_hash": "{row['current_commit'] or 'e4f5a6b'}",
            "environment": "{row['name']}"
        }}
    ]
}}

response = requests.post(
    INTELLI_ENDPOINT,
    json=payload,
    headers={{"X-API-Key": INTELLI_API_KEY}}
)
print("Incident ingestion status:", response.status_code)
print("Analysis response:", response.json().get("risk"), response.json().get("riskScore"))
"""

        node_snippet = f"""// Node.js / TypeScript ingestion snippet
const INTELLI_ENDPOINT = '{ingest_url}';
const INTELLI_API_KEY = '{key_preview}'; // Replace with your full ii_live_... key

async function reportIncident(error, telemetry) {{
  const payload = {{
    title: error.message || 'Unhandled Server Exception',
    service: '{app_slug}',
    status: 'OPEN',
    affected_users_count: telemetry.affectedUsers || 10,
    metrics: {{
      error_rate: telemetry.errorRate || 15.0,
      latency_p99: telemetry.latencyP99 || 850.0,
      deployment_recency_minutes: 60,
      service_criticality: 3
    }},
    logs: [
      {{
        log_level: 'ERROR',
        message: error.message,
        stack_trace: error.stack
      }}
    ],
    deployments: [
      {{
        commit_hash: process.env.GIT_COMMIT_SHA || '{row['current_commit'] or 'c3d4e5f'}',
        environment: '{row['name']}'
      }}
    ]
  }};

  const res = await fetch(INTELLI_ENDPOINT, {{
    method: 'POST',
    headers: {{
      'Content-Type': 'application/json',
      'X-API-Key': INTELLI_API_KEY
    }},
    body: JSON.stringify(payload)
  }});

  const analysis = await res.json();
  console.log('IntelliIncident scored incident risk:', analysis.risk, analysis.riskScore);
}}
"""

        github_actions_snippet = f"""# .github/workflows/deploy.yml
# Correlates deployment commits with runtime incidents in IntelliIncident
name: Production Deployment

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Deploy Application
        run: |
          echo "Deploying ${{ github.sha }} to {row['name']}..."

      - name: Notify IntelliIncident Deployment Evidence
        env:
          INTELLI_KEY: ${{{{ secrets.INTELLIINCIDENT_API_KEY }}}} # Set to your {key_preview}
        run: |
          curl -X POST "{ingest_url}" \\
            -H "Content-Type: application/json" \\
            -H "X-API-Key: $INTELLI_KEY" \\
            -d '{{
              "title": "Deployment Release Notification",
              "service": "{app_slug}",
              "summary": "Automated deployment of commit ${{ github.sha }}",
              "status": "RESOLVED",
              "affected_users_count": 0,
              "metrics": {{
                "error_rate": 0.0,
                "latency_p99": 45.0,
                "deployment_recency_minutes": 0,
                "service_criticality": 3
              }},
              "deployments": [
                {{
                  "commit_hash": "${{ github.sha }}",
                  "environment": "{row['name']}",
                  "author": "${{ github.actor }}",
                  "changelog": "CI/CD automated release"
                }}
              ]
            }}'
"""

        explanation = (
            "IntelliIncident combines runtime telemetry with GitHub repository intelligence. "
            "GitHub provides source diffs, file trees, and commit metadata. "
            "Runtime telemetry provides error rates, latency shifts, and exception stack traces. "
            "The deployment commit hash links the runtime failure to the exact source lines responsible."
        )

        return ConnectionGuideResponse(
            environment_id=row["id"],
            environment_name=row["name"],
            application_id=row["application_id"],
            application_name=row["app_name"],
            project_id=row["proj_id"],
            project_name=row["proj_name"],
            ingestion_endpoint=ingest_url,
            api_key_preview=key_preview,
            curl_snippet=curl_snippet,
            python_snippet=python_snippet,
            node_snippet=node_snippet,
            github_actions_snippet=github_actions_snippet,
            explanation=explanation,
        )
