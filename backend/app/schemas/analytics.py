from typing import List, Dict, Literal
from pydantic import BaseModel

class AnomalyResult(BaseModel):
    detected: bool
    score: float
    threshold: float
    model: Literal["Isolation Forest"] = "Isolation Forest"
    featuresAnalyzed: List[str]
    evaluatedAt: str
    baselineMean: float
    observedDeviation: str

class ClassProbabilities(BaseModel):
    low: float
    medium: float
    high: float
    critical: float

class SeverityPrediction(BaseModel):
    predictedSeverity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    confidence: float
    model: Literal["Random Forest"] = "Random Forest"
    classProbabilities: ClassProbabilities

class FeatureImportance(BaseModel):
    feature: str
    importance: float
    category: str

class MLMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1Score: float
    trainingSamplesCount: int
    lastTrainedDate: str

class ConfusionMatrixRow(BaseModel):
    actual: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    low: int
    medium: int
    high: int
    critical: int

class AnomalyDistributionBin(BaseModel):
    bin: str
    normalCount: int
    anomalyCount: int
    scoreRange: str
