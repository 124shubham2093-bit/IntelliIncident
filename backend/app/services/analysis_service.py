"""
Dynamic Analysis Orchestration Service for IntelliIncident
Coordinates the end-to-end incident intelligence pipeline:
Feature Extraction -> Isolation Forest -> Random Forest -> Fuzzy Risk -> RCA -> Playbooks
"""

import datetime
from typing import Dict, Any, Optional
from backend.app.services.incident_service import IncidentService

class AnalysisService:
    def __init__(self):
        self.incident_service = IncidentService()

    def analyze_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        details = self.incident_service.get_incident_details(incident_id)
        if not details:
            return None

        return {
            "incidentId": incident_id,
            "analyzedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "anomaly": details["mlAnalysis"]["anomaly"],
            "severityPrediction": details["mlAnalysis"]["severityPrediction"],
            "fuzzyRisk": details["fuzzyRisk"],
            "rootCauses": details["rootCauseCandidates"],
            "recommendations": details["recommendations"],
        }
