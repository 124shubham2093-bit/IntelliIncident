from typing import List
from pydantic import BaseModel

from backend.app.schemas.incident import IncidentDetails
from backend.app.schemas.analytics import AnomalyResult, SeverityPrediction
from backend.app.schemas.fuzzy import FuzzyRiskResult
from backend.app.schemas.root_cause import RootCauseCandidate, Recommendation

class IncidentReportResponse(BaseModel):
    incident: IncidentDetails
    generatedAt: str
    reportId: str
    summaryTitle: str

class IncidentAnalysis(BaseModel):
    incidentId: str
    analyzedAt: str
    anomaly: AnomalyResult
    severityPrediction: SeverityPrediction
    fuzzyRisk: FuzzyRiskResult
    rootCauses: List[RootCauseCandidate]
    recommendations: List[Recommendation]
