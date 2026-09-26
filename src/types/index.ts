// Shared TypeScript Interfaces & Types for IntelliIncident

export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentStatus = 'OPEN' | 'INVESTIGATING' | 'MITIGATED' | 'RESOLVED';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'VERY_HIGH';

export interface Incident {
  id: string;
  title: string;
  service: string;
  severity: IncidentSeverity;
  risk: RiskLevel;
  riskScore: number; // 0 to 100
  anomalyDetected: boolean;
  anomalyScore: number; // e.g. -0.42 or 0.85
  status: IncidentStatus;
  timestamp: string; // ISO 8601
  summary: string;
  affectedUsersCount: number;
}

export interface IncidentMetrics {
  service: string;
  affectedUsers: number;
  errorRate: number; // percentage, e.g. 18.4%
  latencyP99: number; // ms, e.g. 1420ms
  latencyP50: number; // ms, e.g. 120ms
  requestVolume: number; // req/sec, e.g. 4500
  deploymentRecencyMinutes: number; // minutes since deployment
  cpuUtilization: number; // percentage
  memoryUtilization: number; // percentage
}

export interface AnomalyResult {
  detected: boolean;
  score: number; // Normalized anomaly score 0.0 - 1.0 or Isolation Forest score
  threshold: number;
  model: 'Isolation Forest';
  featuresAnalyzed: string[];
  evaluatedAt: string;
  baselineMean: number;
  observedDeviation: string;
}

export interface SeverityPrediction {
  predictedSeverity: IncidentSeverity;
  confidence: number; // e.g. 0.89
  model: 'Random Forest';
  classProbabilities: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
}

export interface FuzzyInputValues {
  errorRate: number; // 0 - 100%
  userImpact: number; // 0 - 100 (normalized scale)
  latency: number; // 0 - 3000ms
  deploymentRecency: number; // 0 - 120 minutes (lower is more recent)
  serviceCriticality: number; // 1 - 5 or 0 - 100
}

export interface TriggeredFuzzyRule {
  id: string;
  ruleText: string;
  weight: number; // activation strength 0.0 - 1.0
  contribution: string;
}

export interface FuzzyRiskResult {
  riskScore: number; // 0 - 100
  riskLevel: RiskLevel;
  inputs: {
    errorRateState: 'LOW' | 'MEDIUM' | 'HIGH';
    userImpactState: 'LOW' | 'MEDIUM' | 'HIGH';
    latencyState: 'LOW' | 'MEDIUM' | 'HIGH';
    deploymentRecencyState: 'RECENT' | 'MODERATE' | 'OLD';
    serviceCriticalityState: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  triggeredRules: TriggeredFuzzyRule[];
  defuzzificationMethod: 'Centroid of Area (COA)';
}

export type EventType =
  | 'DEPLOYMENT'
  | 'ERROR_SPIKE'
  | 'LATENCY_INCREASE'
  | 'MONITORING_ALERT'
  | 'SUPPORT_TICKET_SPIKE'
  | 'CONFIG_CHANGE'
  | 'TRAFFIC_SURGE';

export interface EvidenceEvent {
  id: string;
  timestamp: string;
  eventType: EventType;
  service: string;
  description: string;
  severity?: 'INFO' | 'WARN' | 'CRITICAL';
  metadata?: Record<string, string | number>;
}

export interface RootCauseCandidate {
  id: string;
  candidate: string; // e.g. "Recent Deployment", "Database Connection Pool Exhaustion", etc.
  score: number; // 0.0 - 1.0 probability / confidence
  evidence: string[];
  explanation: string;
  category: 'DEPLOYMENT' | 'DATABASE' | 'INFRASTRUCTURE' | 'CODE_ERROR' | 'TRAFFIC' | 'NETWORK';
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  category: 'INVESTIGATION' | 'MITIGATION' | 'ROLLBACK' | 'VERIFICATION';
  actionCmd?: string;
}

export interface IncidentDetails extends Incident {
  metrics: IncidentMetrics;
  mlAnalysis: {
    anomaly: AnomalyResult;
    severityPrediction: SeverityPrediction;
  };
  fuzzyRisk: FuzzyRiskResult;
  evidenceTimeline: EvidenceEvent[];
  rootCauseCandidates: RootCauseCandidate[];
  recommendations: Recommendation[];
}

export interface ServiceHealth {
  service: string;
  status: 'HEALTHY' | 'DEGRADED' | 'OUTAGE';
  errorRate: number; // percentage
  latency: number; // ms
  lastDeployment: string; // e.g. "18 mins ago"
  tier: 'Tier 1' | 'Tier 2' | 'Tier 3';
}

export interface FeatureImportance {
  feature: string;
  importance: number; // 0.0 - 1.0
  category: string;
}

export interface MLMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  trainingSamplesCount: number;
  lastTrainedDate: string;
}

export interface ConfusionMatrixRow {
  actual: IncidentSeverity;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface SystemStatus {
  frontendStatus: 'READY' | 'DEGRADED';
  apiStatus: 'CONNECTED' | 'DISCONNECTED';
  mlModelsStatus: 'READY' | 'PENDING' | 'ERROR';
  fuzzyEngineStatus: 'READY' | 'PENDING' | 'ERROR';
  backendUrl: string;
  lastChecked: string;
}

export interface IncidentAnalysis {
  incidentId: string;
  analyzedAt: string;
  anomaly: AnomalyResult;
  severityPrediction: SeverityPrediction;
  fuzzyRisk: FuzzyRiskResult;
  rootCauses: RootCauseCandidate[];
  recommendations: Recommendation[];
}
