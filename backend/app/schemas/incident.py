from typing import List, Literal, Optional
from pydantic import BaseModel

from backend.app.schemas.analytics import AnomalyResult, SeverityPrediction
from backend.app.schemas.fuzzy import FuzzyRiskResult
from backend.app.schemas.root_cause import EvidenceEvent, RootCauseCandidate, Recommendation
from backend.app.schemas.github import GitHubCommitDetail

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
    project_id: Optional[str] = None
    application_id: Optional[str] = None
    environment_id: Optional[str] = None
    projectId: Optional[str] = None
    applicationId: Optional[str] = None
    environmentId: Optional[str] = None

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
    githubCommits: Optional[List[GitHubCommitDetail]] = None

class TelemetryInput(BaseModel):
    error_rate: float
    latency_p99: float
    latency_p50: float = 60.0
    affected_users: int = 0
    request_volume: int = 1000
    deployment_recency_minutes: int = 180
    cpu_utilization: float = 35.0
    memory_utilization: float = 40.0
    service_criticality: int = 3

class RuntimeLogInput(BaseModel):
    timestamp: Optional[str] = None
    log_level: str = "ERROR"
    message: str
    stack_trace: Optional[str] = None

class DeploymentInput(BaseModel):
    commit_hash: str = "main"
    deployed_at: Optional[str] = None
    environment: str = "production"
    status: str = "SUCCESS"
    author: str = "system"
    changelog: str = "Service deployment update"

class SupportTicketInput(BaseModel):
    created_at: Optional[str] = None
    customer_tier: str = "Enterprise"
    subject: str
    sentiment: str = "NEGATIVE"

class EvidenceEventInput(BaseModel):
    timestamp: Optional[str] = None
    event_type: str = "ALERT"
    service: Optional[str] = None
    description: str
    severity: str = "HIGH"

class IncidentCreatePayload(BaseModel):
    id: Optional[str] = None
    title: str
    service: str
    summary: Optional[str] = None
    status: IncidentStatus = "OPEN"
    timestamp: Optional[str] = None
    affected_users_count: Optional[int] = None
    project_id: Optional[str] = None
    application_id: Optional[str] = None
    environment_id: Optional[str] = None
    projectId: Optional[str] = None
    applicationId: Optional[str] = None
    environmentId: Optional[str] = None
    metrics: Optional[TelemetryInput] = None
    logs: Optional[List[RuntimeLogInput]] = None
    deployments: Optional[List[DeploymentInput]] = None
    tickets: Optional[List[SupportTicketInput]] = None
    events: Optional[List[EvidenceEventInput]] = None

