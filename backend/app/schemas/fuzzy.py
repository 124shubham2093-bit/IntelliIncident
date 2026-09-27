from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class FuzzyInputValues(BaseModel):
    errorRate: float = Field(..., ge=0.0, le=100.0)
    userImpact: float = Field(..., ge=0.0, le=100.0)
    latency: float = Field(..., ge=0.0, le=10000.0)
    deploymentRecency: float = Field(..., ge=0.0, le=10000.0)
    serviceCriticality: float = Field(..., ge=1.0, le=5.0)

class TriggeredFuzzyRule(BaseModel):
    id: str
    ruleText: str
    weight: float
    contribution: str

class FuzzyInputsState(BaseModel):
    errorRateState: Literal["LOW", "MEDIUM", "HIGH"]
    userImpactState: Literal["LOW", "MEDIUM", "HIGH"]
    latencyState: Literal["LOW", "MEDIUM", "HIGH"]
    deploymentRecencyState: Literal["RECENT", "MODERATE", "OLD"]
    serviceCriticalityState: Literal["LOW", "MEDIUM", "HIGH"]

class FuzzyRiskResult(BaseModel):
    riskScore: int = Field(..., ge=0, le=100)
    riskLevel: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "VERY_HIGH"]
    inputs: FuzzyInputsState
    triggeredRules: List[TriggeredFuzzyRule]
    defuzzificationMethod: Literal["Centroid of Area (COA)"] = "Centroid of Area (COA)"
