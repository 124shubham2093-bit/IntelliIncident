"""
Incident Data Access Service for IntelliIncident
Handles incident queries, filtering, and detailed record assembly from SQLite.
"""

import datetime
import uuid
import random
import re
from typing import Dict, Any, List, Optional
from backend.app.db.database import get_db_connection
from backend.app.ml.anomaly_detector import AnomalyDetector
from backend.app.ml.severity_classifier import SeverityClassifier
from backend.app.fuzzy.fuzzy_engine import FuzzyRiskEngine
from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.github_service import GitHubService
from backend.app.services.project_service import ProjectService
from backend.app.schemas.incident import IncidentCreatePayload

HEX_COMMIT_REGEX = re.compile(r"^[0-9a-fA-F]{7,40}$")
INVALID_REF_NAMES = {"main", "master", "head", "latest", "default"}

class IncidentService:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.severity_classifier = SeverityClassifier()
        self.fuzzy_engine = FuzzyRiskEngine()
        self.root_cause_engine = RootCauseEngine()
        self.github_service = GitHubService()
        self.project_service = ProjectService()

    @staticmethod
    def _is_valid_commit_hash(sha: Optional[str]) -> bool:
        if not sha or not isinstance(sha, str):
            return False
        sha_clean = sha.strip()
        if sha_clean.lower() in INVALID_REF_NAMES:
            return False
        return bool(HEX_COMMIT_REGEX.match(sha_clean))

    async def _fetch_deployment_commits(
        self,
        deployments: List[Dict[str, Any]],
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        default_branch: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        commits = []
        seen_shas = set()

        # Application-scoped GitHub repository binding with fallback to global settings
        if repo_owner and repo_name:
            gh_service = GitHubService(
                owner=repo_owner,
                repo=repo_name,
                default_branch=default_branch or "main",
            )
        else:
            gh_service = self.github_service

        for dep in deployments:
            sha = dep.get("commit_hash")
            if not self._is_valid_commit_hash(sha):
                continue
            sha_clean = sha.strip()
            if sha_clean in seen_shas:
                continue
            seen_shas.add(sha_clean)
            try:
                commit_detail = await gh_service.get_commit(sha_clean)
                if commit_detail:
                    c_dict = (
                        commit_detail.model_dump()
                        if hasattr(commit_detail, "model_dump")
                        else (commit_detail if isinstance(commit_detail, dict) else {})
                    )
                    commits.append(c_dict)
            except Exception:
                continue
        return commits

    def get_incidents(
        self,
        search: Optional[str] = None,
        severity: Optional[str] = None,
        risk: Optional[str] = None,
        service: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM incidents WHERE 1=1"
        params = []

        if search:
            query += " AND (id LIKE ? OR title LIKE ? OR service LIKE ? OR summary LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term])

        if severity and severity != "ALL":
            query += " AND severity = ?"
            params.append(severity)

        if risk and risk != "ALL":
            query += " AND risk = ?"
            params.append(risk)

        if service and service != "ALL":
            query += " AND service = ?"
            params.append(service)

        if status and status != "ALL":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            keys = r.keys()
            p_id = r["project_id"] if "project_id" in keys else None
            a_id = r["application_id"] if "application_id" in keys else None
            e_id = r["environment_id"] if "environment_id" in keys else None
            result.append({
                "id": r["id"],
                "title": r["title"],
                "service": r["service"],
                "severity": r["severity"],
                "risk": r["risk"],
                "riskScore": r["risk_score"],
                "anomalyDetected": bool(r["anomaly_detected"]),
                "anomalyScore": r["anomaly_score"],
                "status": r["status"],
                "timestamp": r["timestamp"],
                "summary": r["summary"],
                "affectedUsersCount": r["affected_users_count"],
                "projectId": p_id,
                "applicationId": a_id,
                "environmentId": e_id,
                "project_id": p_id,
                "application_id": a_id,
                "environment_id": e_id,
            })
        return result

    async def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        inc_row = cursor.fetchone()
        if not inc_row:
            conn.close()
            return None

        cursor.execute("SELECT * FROM incident_metrics WHERE incident_id = ?", (incident_id,))
        metric_row = cursor.fetchone()

        cursor.execute("SELECT * FROM runtime_logs WHERE incident_id = ? ORDER BY timestamp ASC", (incident_id,))
        log_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM support_tickets WHERE incident_id = ? ORDER BY created_at ASC", (incident_id,))
        ticket_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM evidence_events WHERE incident_id = ? ORDER BY timestamp ASC", (incident_id,))
        event_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM deployments WHERE service = ? ORDER BY deployed_at DESC LIMIT 5", (inc_row["service"],))
        dep_rows = cursor.fetchall()

        conn.close()

        # Build metrics dict
        if metric_row:
            metrics = {
                "service": metric_row["service"],
                "affectedUsers": metric_row["affected_users"],
                "errorRate": metric_row["error_rate"],
                "latencyP99": metric_row["latency_p99"],
                "latencyP50": metric_row["latency_p50"],
                "requestVolume": metric_row["request_volume"],
                "deploymentRecencyMinutes": metric_row["deployment_recency_minutes"],
                "cpuUtilization": metric_row["cpu_utilization"],
                "memoryUtilization": metric_row["memory_utilization"],
            }
            criticality = metric_row["service_criticality"]
        else:
            metrics = {
                "service": inc_row["service"],
                "affectedUsers": inc_row["affected_users_count"],
                "errorRate": 2.5,
                "latencyP99": 240.0,
                "latencyP50": 60.0,
                "requestVolume": 1000,
                "deploymentRecencyMinutes": 180,
                "cpuUtilization": 35.0,
                "memoryUtilization": 40.0,
            }
            criticality = 3

        # Transform logs, tickets, deployments
        logs_list = [dict(lr) for lr in log_rows]
        tickets_list = [dict(tr) for tr in ticket_rows]
        deps_list = [dict(dr) for dr in dep_rows]

        # ML Predictions using real trained models
        telemetry_payload = {
            "error_rate": metrics["errorRate"],
            "latency_p99": metrics["latencyP99"],
            "latency_p50": metrics["latencyP50"],
            "affected_users": metrics["affectedUsers"],
            "cpu_utilization": metrics["cpuUtilization"],
            "memory_utilization": metrics["memoryUtilization"],
            "deployment_recency_minutes": metrics["deploymentRecencyMinutes"],
            "request_volume": metrics["requestVolume"],
            "service_criticality": criticality,
        }

        anomaly_res = self.anomaly_detector.predict(telemetry_payload)
        severity_res = self.severity_classifier.predict(telemetry_payload)

        # Fuzzy Risk Evaluation using real Mamdani engine
        fuzzy_inputs = {
            "errorRate": metrics["errorRate"],
            "userImpact": min(int((metrics["affectedUsers"] / 5000.0) * 100), 100),
            "latency": metrics["latencyP99"],
            "deploymentRecency": metrics["deploymentRecencyMinutes"],
            "serviceCriticality": criticality,
        }
        fuzzy_res = self.fuzzy_engine.evaluate(fuzzy_inputs)

        # Evidence timeline
        evidence_timeline = []
        for ev in event_rows:
            evidence_timeline.append({
                "id": ev["id"],
                "timestamp": ev["timestamp"],
                "eventType": ev["event_type"],
                "service": ev["service"],
                "description": ev["description"],
                "severity": ev["severity"],
            })

        # Root Cause Analysis with GitHub Commit Evidence
        incident_dict = dict(inc_row)
        inc_keys = inc_row.keys()
        p_id = inc_row["project_id"] if "project_id" in inc_keys else None
        a_id = inc_row["application_id"] if "application_id" in inc_keys else None
        e_id = inc_row["environment_id"] if "environment_id" in inc_keys else None

        # Resolve application-scoped GitHub repo
        repo_owner = None
        repo_name = None
        default_branch = None
        if a_id:
            app_rec = self.project_service.get_application_by_id(a_id)
            if app_rec and app_rec.get("repo_owner") and app_rec.get("repo_name"):
                repo_owner = app_rec["repo_owner"]
                repo_name = app_rec["repo_name"]
                default_branch = app_rec.get("default_branch") or "main"
        if not repo_owner:
            app_resolved = self.project_service.resolve_service_application(inc_row["service"])
            if app_resolved:
                if not a_id:
                    a_id = app_resolved["id"]
                if not p_id:
                    p_id = app_resolved["project_id"]
                if app_resolved.get("repo_owner") and app_resolved.get("repo_name"):
                    repo_owner = app_resolved["repo_owner"]
                    repo_name = app_resolved["repo_name"]
                    default_branch = app_resolved.get("default_branch") or "main"

        github_commits = await self._fetch_deployment_commits(
            deps_list,
            repo_owner=repo_owner,
            repo_name=repo_name,
            default_branch=default_branch,
        )
        root_causes = self.root_cause_engine.analyze(
            incident=incident_dict,
            metrics=metrics,
            logs=logs_list,
            deployments=deps_list,
            tickets=tickets_list,
            github_commits=github_commits,
        )

        # Recommendations based on top candidate
        top_cand = root_causes[0] if root_causes else {"category": "CODE_ERROR"}
        recommendations = RecommendationService.generate_recommendations(
            top_candidate=top_cand,
            service_name=inc_row["service"],
            severity=inc_row["severity"],
            github_commits=github_commits,
        )

        return {
            "id": inc_row["id"],
            "title": inc_row["title"],
            "service": inc_row["service"],
            "severity": inc_row["severity"],
            "risk": inc_row["risk"],
            "riskScore": inc_row["risk_score"],
            "anomalyDetected": bool(inc_row["anomaly_detected"]),
            "anomalyScore": inc_row["anomaly_score"],
            "status": inc_row["status"],
            "timestamp": inc_row["timestamp"],
            "summary": inc_row["summary"],
            "affectedUsersCount": inc_row["affected_users_count"],
            "projectId": p_id,
            "applicationId": a_id,
            "environmentId": e_id,
            "project_id": p_id,
            "application_id": a_id,
            "environment_id": e_id,
            "metrics": metrics,
            "mlAnalysis": {
                "anomaly": anomaly_res,
                "severityPrediction": severity_res,
            },
            "fuzzyRisk": fuzzy_res,
            "evidenceTimeline": evidence_timeline,
            "rootCauseCandidates": root_causes,
            "recommendations": recommendations,
            "githubCommits": github_commits,
        }

    async def create_incident(self, payload: IncidentCreatePayload) -> Dict[str, Any]:
        """
        Ingest a real or developer-supplied incident, execute the full intelligence
        pipeline (Feature Engineering -> Isolation Forest -> Random Forest -> Fuzzy Risk -> RCA),
        persist to SQLite, and return the complete analyzed incident.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        incident_id = payload.id.strip() if payload.id and payload.id.strip() else f"INC-{random.randint(1000, 9999)}"
        timestamp = payload.timestamp or now_iso

        if payload.metrics:
            m = payload.metrics
            error_rate = float(m.error_rate)
            latency_p99 = float(m.latency_p99)
            latency_p50 = float(m.latency_p50)
            affected_users = int(m.affected_users)
            request_volume = int(m.request_volume)
            deployment_recency = int(m.deployment_recency_minutes)
            cpu_utilization = float(m.cpu_utilization)
            memory_utilization = float(m.memory_utilization)
            service_criticality = int(m.service_criticality)
        else:
            error_rate = 2.5
            latency_p99 = 240.0
            latency_p50 = 60.0
            affected_users = payload.affected_users_count or 0
            request_volume = 1000
            deployment_recency = 180
            cpu_utilization = 35.0
            memory_utilization = 40.0
            service_criticality = 3

        telemetry_payload = {
            "error_rate": error_rate,
            "latency_p99": latency_p99,
            "latency_p50": latency_p50,
            "affected_users": affected_users,
            "cpu_utilization": cpu_utilization,
            "memory_utilization": memory_utilization,
            "deployment_recency_minutes": deployment_recency,
            "request_volume": request_volume,
            "service_criticality": service_criticality,
        }

        # 1. ML Anomaly Detection (Isolation Forest)
        anomaly_res = self.anomaly_detector.predict(telemetry_payload)
        anomaly_detected = 1 if anomaly_res.get("detected", False) else 0
        anomaly_score = float(anomaly_res.get("score", 0.0))

        # 2. ML Severity Classification (Random Forest)
        severity_res = self.severity_classifier.predict(telemetry_payload)
        predicted_severity = severity_res.get("predictedSeverity", "LOW")

        # 3. Fuzzy Risk Assessment (Mamdani FIS with scikit-fuzzy)
        fuzzy_inputs = {
            "errorRate": error_rate,
            "userImpact": min(int((affected_users / 5000.0) * 100), 100),
            "latency": latency_p99,
            "deploymentRecency": deployment_recency,
            "serviceCriticality": service_criticality,
        }
        fuzzy_res = self.fuzzy_engine.evaluate(fuzzy_inputs)
        risk_score = int(fuzzy_res.get("riskScore", 0))
        risk_level = str(fuzzy_res.get("riskLevel", "LOW"))

        # 4. Process evidence collections
        logs_list = []
        if payload.logs:
            for idx, l in enumerate(payload.logs):
                logs_list.append({
                    "id": f"LOG-{incident_id}-{idx+1}",
                    "incident_id": incident_id,
                    "timestamp": l.timestamp or timestamp,
                    "log_level": l.log_level,
                    "message": l.message,
                    "stack_trace": l.stack_trace,
                })

        deps_list = []
        if payload.deployments:
            for idx, d in enumerate(payload.deployments):
                deps_list.append({
                    "id": f"DEP-{incident_id}-{idx+1}",
                    "service": payload.service,
                    "commit_hash": d.commit_hash,
                    "deployed_at": d.deployed_at or timestamp,
                    "environment": d.environment,
                    "status": d.status,
                    "author": d.author,
                    "changelog": d.changelog,
                })

        tickets_list = []
        if payload.tickets:
            for idx, t in enumerate(payload.tickets):
                tickets_list.append({
                    "id": f"TCK-{incident_id}-{idx+1}",
                    "incident_id": incident_id,
                    "created_at": t.created_at or timestamp,
                    "customer_tier": t.customer_tier,
                    "subject": t.subject,
                    "sentiment": t.sentiment,
                })

        events_list = []
        if payload.events:
            for idx, e in enumerate(payload.events):
                events_list.append({
                    "id": f"EVT-{incident_id}-{idx+1}",
                    "incident_id": incident_id,
                    "timestamp": e.timestamp or timestamp,
                    "event_type": e.event_type,
                    "service": e.service or payload.service,
                    "description": e.description,
                    "severity": e.severity,
                })

        # 5. Root Cause Analysis
        metrics_dict = {
            "service": payload.service,
            "affectedUsers": affected_users,
            "errorRate": error_rate,
            "latencyP99": latency_p99,
            "latencyP50": latency_p50,
            "requestVolume": request_volume,
            "deploymentRecencyMinutes": deployment_recency,
            "cpuUtilization": cpu_utilization,
            "memoryUtilization": memory_utilization,
        }
        temp_inc = {
            "id": incident_id,
            "service": payload.service,
            "title": payload.title,
            "severity": predicted_severity,
        }

        # Resolve topology associations
        p_id = payload.project_id or payload.projectId
        a_id = payload.application_id or payload.applicationId
        e_id = payload.environment_id or payload.environmentId

        if not a_id:
            resolved_app = self.project_service.resolve_service_application(payload.service)
            if resolved_app:
                a_id = resolved_app["id"]
                if not p_id:
                    p_id = resolved_app["project_id"]

        repo_owner = None
        repo_name = None
        default_branch = None
        if a_id:
            app_rec = self.project_service.get_application_by_id(a_id)
            if app_rec and app_rec.get("repo_owner") and app_rec.get("repo_name"):
                repo_owner = app_rec["repo_owner"]
                repo_name = app_rec["repo_name"]
                default_branch = app_rec.get("default_branch") or "main"

        github_commits = await self._fetch_deployment_commits(
            deps_list,
            repo_owner=repo_owner,
            repo_name=repo_name,
            default_branch=default_branch,
        )
        root_causes = self.root_cause_engine.analyze(
            incident=temp_inc,
            metrics=metrics_dict,
            logs=logs_list,
            deployments=deps_list,
            tickets=tickets_list,
            github_commits=github_commits,
        )
        top_category = root_causes[0]["category"] if root_causes else "CODE_ERROR"

        summary = payload.summary or f"{payload.title} impacting {payload.service}."
        affected_users_count = payload.affected_users_count if payload.affected_users_count is not None else affected_users

        # 6. Persist to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert or replace incident record
        cursor.execute("""
        INSERT OR REPLACE INTO incidents (
            id, title, service, severity, risk, risk_score,
            anomaly_detected, anomaly_score, status, timestamp,
            summary, affected_users_count, root_cause_category,
            project_id, application_id, environment_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id,
            payload.title,
            payload.service,
            predicted_severity,
            risk_level,
            risk_score,
            anomaly_detected,
            anomaly_score,
            payload.status,
            timestamp,
            summary,
            affected_users_count,
            top_category,
            p_id,
            a_id,
            e_id,
        ))

        # Insert or replace metrics record
        cursor.execute("""
        INSERT OR REPLACE INTO incident_metrics (
            incident_id, service, affected_users, error_rate,
            latency_p99, latency_p50, request_volume,
            deployment_recency_minutes, cpu_utilization,
            memory_utilization, service_criticality
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id,
            payload.service,
            affected_users,
            error_rate,
            latency_p99,
            latency_p50,
            request_volume,
            deployment_recency,
            cpu_utilization,
            memory_utilization,
            service_criticality,
        ))

        # Insert associated evidence
        for log in logs_list:
            cursor.execute("""
            INSERT OR REPLACE INTO runtime_logs (id, incident_id, timestamp, log_level, message, stack_trace)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (log["id"], log["incident_id"], log["timestamp"], log["log_level"], log["message"], log["stack_trace"]))

        for dep in deps_list:
            cursor.execute("""
            INSERT OR REPLACE INTO deployments (id, service, commit_hash, deployed_at, environment, status, author, changelog)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (dep["id"], dep["service"], dep["commit_hash"], dep["deployed_at"], dep["environment"], dep["status"], dep["author"], dep["changelog"]))

        for tck in tickets_list:
            cursor.execute("""
            INSERT OR REPLACE INTO support_tickets (id, incident_id, created_at, customer_tier, subject, sentiment)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (tck["id"], tck["incident_id"], tck["created_at"], tck["customer_tier"], tck["subject"], tck["sentiment"]))

        for evt in events_list:
            cursor.execute("""
            INSERT OR REPLACE INTO evidence_events (id, incident_id, timestamp, event_type, service, description, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (evt["id"], evt["incident_id"], evt["timestamp"], evt["event_type"], evt["service"], evt["description"], evt["severity"]))

        conn.commit()
        conn.close()

        return await self.get_incident_details(incident_id)

