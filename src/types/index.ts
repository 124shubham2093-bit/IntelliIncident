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
  projectId?: string | null;
  applicationId?: string | null;
  environmentId?: string | null;
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
  githubCommits?: GitHubCommitDetail[];
  githubSourceEvidence?: GitHubSourceEvidence | null;
  deployedCommit?: string | null;
  environmentName?: string | null;
  sentryEvidence?: SentryEvidence | null;
  prometheusEvidence?: PrometheusEvidence | null;
  prometheus_evidence?: PrometheusEvidence | null;
  jiraEvidence?: JiraEvidence | null;
  jira_evidence?: JiraEvidence | null;
}

// GitHub Code Intelligence Types
export interface GitHubRateLimit {
  limit: number;
  remaining: number;
  reset_at: number | null;
  used: number;
}

export interface GitHubStatus {
  configured: boolean;
  authenticated: boolean;
  reachable: boolean;
  owner: string;
  repo: string;
  default_branch: string;
  api_url: string;
  rate_limit?: GitHubRateLimit | null;
  message?: string | null;
}

export interface GitHubRepository {
  full_name: string;
  owner: string;
  name: string;
  description?: string | null;
  default_branch: string;
  is_private: boolean;
  html_url: string;
  stars_count: number;
  forks_count: number;
  open_issues_count: number;
}

export interface GitHubCommitAuthor {
  name?: string | null;
  email?: string | null;
  date?: string | null;
  username?: string | null;
  avatar_url?: string | null;
}

export interface GitHubCommitSummary {
  sha: string;
  short_sha: string;
  message: string;
  author: GitHubCommitAuthor;
  committed_at?: string | null;
  html_url: string;
}

export interface GitHubChangedFile {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  blob_url?: string | null;
  raw_url?: string | null;
  patch?: string | null;
}

export interface GitHubCommitDetail extends GitHubCommitSummary {
  stats: {
    total: number;
    additions: number;
    deletions: number;
  };
  files: GitHubChangedFile[];
}

export interface GitHubFileContent {
  path: string;
  name: string;
  size: number;
  sha: string;
  html_url?: string | null;
  encoding?: string | null;
  content?: string | null;
  decoded_content?: string | null;
  is_binary: boolean;
}

export interface GitHubApplicationVerification {
  connected: boolean;
  repository_accessible: boolean;
  branch_accessible: boolean;
  owner: string;
  repo: string;
  branch: string;
  default_branch?: string | null;
  message?: string | null;
  rate_limit?: GitHubRateLimit | null;
}

export interface GitHubSourceLocation {
  file_path: string;
  line_number: number;
  column_number?: number | null;
  function_name?: string | null;
}

export interface GitHubSourceLine {
  line_number: number;
  content: string;
  is_target: boolean;
}

export interface GitHubSourceEvidence {
  status: string; // "MATCHED", "UNRESOLVED", "FILE_NOT_FOUND", "GITHUB_UNAVAILABLE", "NO_STACK_TRACE", "NO_COMMIT"
  deployment_commit?: string | null;
  location?: GitHubSourceLocation | null;
  repo_owner?: string | null;
  repo_name?: string | null;
  file_path?: string | null;
  target_line?: number | null;
  source_lines?: GitHubSourceLine[] | null;
  raw_code?: string | null;
  message: string;
}

// ==========================================
// Sentry Runtime Error Intelligence Types
// ==========================================

export interface SentryRateLimit {
  limit: number;
  remaining: number;
  reset_at?: number | null;
  concurrent?: number | null;
}

export interface SentryStatus {
  configured: boolean;
  authenticated: boolean;
  reachable: boolean;
  org_slug?: string | null;
  project_slug?: string | null;
  base_url: string;
  rate_limit?: SentryRateLimit | null;
  message?: string | null;
}

export interface SentryProject {
  id: string;
  slug: string;
  name: string;
  organization_slug: string;
  platform?: string | null;
  is_active: boolean;
  has_access: boolean;
}

export interface SentryStackFrame {
  filename?: string | null;
  function?: string | null;
  module?: string | null;
  lineno?: number | null;
  colno?: number | null;
  context_line?: string | null;
  in_app: boolean;
}

export interface SentryException {
  type: string;
  value: string;
  module?: string | null;
  frames: SentryStackFrame[];
}

export interface SentryTag {
  key: string;
  value: string;
}

export interface SentryEvent {
  id: string;
  event_id: string;
  title?: string | null;
  message?: string | null;
  timestamp?: string | null;
  platform?: string | null;
  environment?: string | null;
  release?: string | null;
  culprit?: string | null;
  exceptions: SentryException[];
  tags: SentryTag[];
  permalink?: string | null;
}

export interface SentryIssue {
  id: string;
  short_id?: string | null;
  title: string;
  culprit?: string | null;
  type?: string | null;
  level?: string | null;
  count: number;
  user_count: number;
  first_seen?: string | null;
  last_seen?: string | null;
  permalink?: string | null;
  status?: string | null;
  metadata?: Record<string, any>;
  latest_event?: SentryEvent | null;
}

export interface SentryEvidence {
  status: string; // "CONNECTED" | "NO_ISSUES_FOUND" | "NOT_CONFIGURED" | "UNAVAILABLE" | "AUTH_ERROR" | "RATE_LIMITED"
  org_slug?: string | null;
  project_slug?: string | null;
  issue_count: number;
  issues: SentryIssue[];
  latest_issue?: SentryIssue | null;
  latest_event?: SentryEvent | null;
  matched_exception_type?: string | null;
  matched_exception_value?: string | null;
  matched_stack_trace_frames: SentryStackFrame[];
  correlated_release?: string | null;
  correlated_environment?: string | null;
  message: string;
}

// ==========================================
// Prometheus Metric Telemetry Types
// ==========================================

export interface PrometheusStatus {
  status: 'CONNECTED' | 'NOT_CONFIGURED' | 'UNAVAILABLE' | 'ERROR';
  url: string;
  reachable: boolean;
  version?: string | null;
  message: string;
}

export interface PrometheusSeriesPoint {
  timestamp: number;
  value: number;
}

export interface PrometheusTimeWindow {
  incident_time: string;
  baseline_start: string;
  baseline_end: string;
  incident_start: string;
  incident_end: string;
}

export interface PrometheusMetricSample {
  metric_name: string;
  query: string;
  unit: string;
  baseline_value?: number | null;
  observed_value?: number | null;
  deviation_pct?: number | null;
  anomaly_detected: boolean;
  correlation_strength: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'AVAILABLE' | 'UNAVAILABLE' | 'NOT_FOUND';
  message?: string | null;
  series?: PrometheusSeriesPoint[];
}

export interface PrometheusEvidence {
  status: string; // "CONNECTED" | "NOT_CONFIGURED" | "UNAVAILABLE" | "NO_METRICS_FOUND" | "ERROR"
  url: string;
  service?: string | null;
  time_window?: PrometheusTimeWindow | null;
  cpu_utilization?: PrometheusMetricSample | null;
  memory_utilization?: PrometheusMetricSample | null;
  request_rate?: PrometheusMetricSample | null;
  error_rate?: PrometheusMetricSample | null;
  p95_latency?: PrometheusMetricSample | null;
  availability?: PrometheusMetricSample | null;
  metrics?: Record<string, PrometheusMetricSample>;
  anomalies_detected: number;
  highest_correlation: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  summary: string;
}

// ==========================================
// Jira Work Item and Incident Ticket Types
// ==========================================

export interface JiraStatus {
  configured: boolean;
  authenticated: boolean;
  reachable: boolean;
  base_url: string;
  email?: string | null;
  project_key?: string | null;
  user_display_name?: string | null;
  server_title?: string | null;
  version?: string | null;
  message: string;
}

export interface JiraIssue {
  id: string;
  key: string;
  summary: string;
  description?: string | null;
  issue_type: string;
  status: string;
  priority: string;
  project_key?: string | null;
  project_name?: string | null;
  labels: string[];
  components: string[];
  assignee?: string | null;
  reporter?: string | null;
  created?: string | null;
  updated?: string | null;
  resolution?: string | null;
  url?: string | null;
}

export interface JiraCorrelationMatch {
  matched_by: string[];
  confidence_score: number;
  explanation: string;
}

export interface JiraEvidence {
  status: string; // "CONNECTED" | "NO_ISSUES_FOUND" | "NOT_CONFIGURED" | "UNAVAILABLE" | "AUTH_ERROR" | "ERROR"
  base_url: string;
  project_key?: string | null;
  total_issues_found: number;
  matched_issues: JiraIssue[];
  primary_issue?: JiraIssue | null;
  correlation?: JiraCorrelationMatch | null;
  correlation_strength: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  summary: string;
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

// ==========================================
// Project, Application, Environment Topology Types
// ==========================================

export interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  application_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  description?: string | null;
  language: string;
  framework?: string | null;
  repo_owner?: string | null;
  repo_name?: string | null;
  default_branch: string;
  environment_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Environment {
  id: string;
  application_id: string;
  name: string;
  slug: string;
  api_key_preview: string;
  api_key?: string | null; // Populated only immediately after creation or regeneration
  endpoint_url?: string | null;
  current_commit?: string | null;
  is_production: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentApiKeyRegenerateResponse {
  id: string;
  api_key: string;
  api_key_preview: string;
  message: string;
}

export interface ConnectionSnippet {
  language: string;
  title: string;
  code: string;
}

export interface ConnectionGuide {
  environment_id: string;
  environment_name: string;
  application_id: string;
  application_name: string;
  project_id: string;
  project_name: string;
  ingestion_endpoint: string;
  api_key_preview: string;
  curl_snippet: string;
  python_snippet: string;
  node_snippet: string;
  github_actions_snippet: string;
  explanation: string;
}

export interface IngestionTestResult {
  status: string;
  environment_id: string;
  environment_name: string;
  application_name: string;
  project_name: string;
  authenticated: boolean;
  message: string;
}
