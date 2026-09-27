"""
Incident Data Access Service for IntelliIncident
Handles incident queries, filtering, and detailed record assembly from SQLite.
"""

from typing import Dict, Any, List, Optional
from backend.app.db.database import get_db_connection
from backend.app.ml.anomaly_detector import AnomalyDetector
from backend.app.ml.severity_classifier import SeverityClassifier
from backend.app.fuzzy.fuzzy_engine import FuzzyRiskEngine
from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.services.recommendation_service import RecommendationService

class IncidentService:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.severity_classifier = SeverityClassifier()
        self.fuzzy_engine = FuzzyRiskEngine()
        self.root_cause_engine = RootCauseEngine()

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
            })
        return result

    def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
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

        # Root Cause Analysis
        incident_dict = dict(inc_row)
        root_causes = self.root_cause_engine.analyze(
            incident=incident_dict,
            metrics=metrics,
            logs=logs_list,
            deployments=deps_list,
            tickets=tickets_list,
        )

        # Recommendations based on top candidate
        top_cand = root_causes[0] if root_causes else {"category": "CODE_ERROR"}
        recommendations = RecommendationService.generate_recommendations(
            top_candidate=top_cand,
            service_name=inc_row["service"],
            severity=inc_row["severity"],
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
            "metrics": metrics,
            "mlAnalysis": {
                "anomaly": anomaly_res,
                "severityPrediction": severity_res,
            },
            "fuzzyRisk": fuzzy_res,
            "evidenceTimeline": evidence_timeline,
            "rootCauseCandidates": root_causes,
            "recommendations": recommendations,
        }
