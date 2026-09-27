from typing import List, Literal, Optional
from pydantic import BaseModel

from backend.app.schemas.analytics import AnomalyResult, SeverityPrediction
from backend.app.schemas.fuzzy import FuzzyRiskResult
from backend.app.schemas.root_cause import EvidenceEvent, RootCauseCandidate, Recommendation

IncidentSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
IncidentStatus = Literal["OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "VERY_HIGH"]

class Incident(BaseModel):
    id: str
    title: str
    service: str
    severity: IncidentSeverity
    risk: RiskLevel
    riskScore: int
    anomalyDetected: bool
    anomalyScore: float
    status: IncidentStatus
    timestamp: str
    summary: str
    affectedUsersCount: int

class IncidentMetrics(BaseModel):
    service: str
    affectedUsers: int
    errorRate: float
    latencyP99: float
    latencyP50: float
    requestVolume: int
    deploymentRecencyMinutes: int
    cpuUtilization: float
    memoryUtilization: float

class MLAnalysisWrapper(BaseModel):
    anomaly: AnomalyResult
    severityPrediction: SeverityPrediction

class IncidentDetails(Incident):
    metrics: IncidentMetrics
    mlAnalysis: MLAnalysisWrapper
    fuzzyRisk: FuzzyRiskResult
    evidenceTimeline: List[EvidenceEvent]
    rootCauseCandidates: List[RootCauseCandidate]
    recommendations: List[Recommendation]
