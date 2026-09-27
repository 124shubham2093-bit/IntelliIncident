from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel

EventType = Literal[
    "DEPLOYMENT",
    "ERROR_SPIKE",
    "LATENCY_INCREASE",
    "MONITORING_ALERT",
    "SUPPORT_TICKET_SPIKE",
    "CONFIG_CHANGE",
    "TRAFFIC_SURGE"
]

class EvidenceEvent(BaseModel):
    id: str
    timestamp: str
    eventType: EventType
    service: str
    description: str
    severity: Optional[Literal["INFO", "WARN", "CRITICAL"]] = "WARN"
    metadata: Optional[Dict[str, Any]] = None

class RootCauseCandidate(BaseModel):
    id: str
    candidate: str
    score: float
    evidence: List[str]
    explanation: str
    category: Literal["DEPLOYMENT", "DATABASE", "INFRASTRUCTURE", "CODE_ERROR", "TRAFFIC", "NETWORK"]

class Recommendation(BaseModel):
    id: str
    title: str
    description: str
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    category: Literal["INVESTIGATION", "MITIGATION", "ROLLBACK", "VERIFICATION"]
    actionCmd: Optional[str] = None
