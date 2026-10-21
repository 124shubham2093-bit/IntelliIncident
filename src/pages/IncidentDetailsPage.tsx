import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  SearchCode,
  Activity,
  BrainCircuit,
  FileText,
  GitCommit,
  FileCode,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { EvidenceTimeline } from '@/components/Incident/EvidenceTimeline';
import { RootCauseList } from '@/components/Incident/RootCauseList';
import { RecommendationsList } from '@/components/Incident/RecommendationsList';
import { GitHubCommitCard } from '@/components/Incident/GitHubCommitCard';
import { SentryEvidenceCard } from '@/components/Incident/SentryEvidenceCard';
import { PrometheusEvidenceCard } from '@/components/Incident/PrometheusEvidenceCard';
import { JiraEvidenceCard } from '@/components/Incident/JiraEvidenceCard';
import { getIncidentById } from '@/api/incidents';
import { IncidentDetails } from '@/types';

export const IncidentDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<IncidentDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!id) return;
      setLoading(true);
      const res = await getIncidentById(id);
      setIncident(res.data);
      setLoading(false);
    }
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="py-24 text-center text-sm text-slate-500 dark:text-slate-400 font-sans">
        Loading incident details...
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="py-24 text-center text-sm text-red-600 dark:text-red-400 font-sans">
        Incident {id} not found.
      </div>
    );
  }

  const { metrics, mlAnalysis, fuzzyRisk } = incident;

  return (
    <div className="space-y-6">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={() => navigate('/incidents')}
          className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors cursor-pointer font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Incidents</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate('/investigation')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-medium transition-colors shadow-xs cursor-pointer"
          >
            <SearchCode className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span>Investigation</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/reports')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-medium transition-colors shadow-xs cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
            <span>Post-Mortem Report</span>
          </button>
        </div>
      </div>

      {/* Incident Header Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-2xl font-bold font-mono text-blue-600 dark:text-blue-400">{incident.id}</span>
              <SeverityBadge severity={incident.severity} />
              <RiskBadge risk={incident.risk} score={incident.riskScore} showScore />
              <StatusBadge status={incident.status} />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 font-sans tracking-tight">
              {incident.title}
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed max-w-3xl">
              {incident.summary}
            </p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 p-4 rounded-lg text-xs space-y-2 shrink-0 min-w-[260px]">
            <div className="flex justify-between text-slate-600 dark:text-slate-400">
              <span className="text-slate-500 dark:text-slate-400">Service:</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">{incident.service}</span>
            </div>
            {incident.projectId && (
              <div className="flex justify-between text-slate-600 dark:text-slate-400">
                <span className="text-slate-500 dark:text-slate-400">Project:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">{incident.projectId}</span>
              </div>
            )}
            {incident.environmentId && (
              <div className="flex justify-between text-slate-600 dark:text-slate-400">
                <span className="text-slate-500 dark:text-slate-400">Environment:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">{incident.environmentName || incident.environmentId}</span>
              </div>
            )}
            {incident.deployedCommit && (
              <div className="flex justify-between text-slate-600 dark:text-slate-400">
                <span className="text-slate-500 dark:text-slate-400">Deployed Commit:</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                  {incident.deployedCommit.slice(0, 7)}
                </span>
              </div>
            )}
            <div className="flex justify-between text-slate-600 dark:text-slate-400">
              <span className="text-slate-500 dark:text-slate-400">Timestamp:</span>
              <span className="text-slate-800 dark:text-slate-200">{incident.timestamp.substring(0, 16).replace('T', ' ')} UTC</span>
            </div>
            <div className="flex justify-between text-slate-600 dark:text-slate-400">
              <span className="text-slate-500 dark:text-slate-400">ML Anomaly:</span>
              <span className={`font-semibold ${incident.anomalyDetected ? 'text-red-600 dark:text-red-400' : 'text-slate-700 dark:text-slate-300'}`}>
                {incident.anomalyDetected ? 'Detected' : 'Normal'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* INVESTIGATION WORKFLOW STEPPER */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4 shadow-xs overflow-x-auto">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
          Investigation Workflow Pipeline
        </div>
        <div className="flex items-center gap-2 text-xs font-sans min-w-[760px]">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium">
            <span className="w-5 h-5 rounded-full bg-white dark:bg-slate-700 text-xs flex items-center justify-center font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">1</span>
            <span>Telemetry Ingestion</span>
          </div>
          <span className="text-slate-400 dark:text-slate-600 font-bold">&rarr;</span>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium">
            <span className="w-5 h-5 rounded-full bg-white dark:bg-slate-700 text-xs flex items-center justify-center font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">2</span>
            <span>ML Outlier & Severity</span>
          </div>
          <span className="text-slate-400 dark:text-slate-600 font-bold">&rarr;</span>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium">
            <span className="w-5 h-5 rounded-full bg-white dark:bg-slate-700 text-xs flex items-center justify-center font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">3</span>
            <span>Mamdani Fuzzy Risk</span>
          </div>
          <span className="text-slate-400 dark:text-slate-600 font-bold">&rarr;</span>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium">
            <span className="w-5 h-5 rounded-full bg-white dark:bg-slate-700 text-xs flex items-center justify-center font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">4</span>
            <span>Multi-Source Evidence</span>
          </div>
          <span className="text-slate-400 dark:text-slate-600 font-bold">&rarr;</span>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium">
            <span className="w-5 h-5 rounded-full bg-white dark:bg-slate-700 text-xs flex items-center justify-center font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">5</span>
            <span>Root Cause Engine</span>
          </div>
          <span className="text-slate-400 dark:text-slate-600 font-bold">&rarr;</span>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 text-blue-700 dark:text-blue-300 font-semibold">
            <span className="w-5 h-5 rounded-full bg-blue-600 text-xs flex items-center justify-center font-bold text-white">6</span>
            <span>Prescriptive Actions</span>
          </div>
        </div>
      </div>

      {/* SECTION 1: Operational Telemetry */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Operational Telemetry
            </h3>
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400">Incident Baseline</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium block">Service</span>
            <span className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1 block truncate">
              {metrics.service}
            </span>
            {incident.environmentId && (
              <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 block truncate">
                Env: {incident.environmentId}
              </span>
            )}
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium block">
              Affected Users
            </span>
            <span className="text-sm font-bold text-red-600 dark:text-red-400 mt-1 block">
              {metrics.affectedUsers.toLocaleString()}
            </span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium block">
              Error Rate
            </span>
            <span className="text-sm font-bold text-red-600 dark:text-red-400 mt-1 block">
              {metrics.errorRate}%
            </span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium block">
              P99 Latency
            </span>
            <span className="text-sm font-bold text-amber-600 dark:text-amber-400 mt-1 block">
              {metrics.latencyP99}ms
            </span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium block">
              Request Volume
            </span>
            <span className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1 block">
              {metrics.requestVolume.toLocaleString()} req/s
            </span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium block">
              Deployment Recency
            </span>
            <span className="text-sm font-bold text-blue-600 dark:text-blue-400 mt-1 block">
              {metrics.deploymentRecencyMinutes}m ago
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 2: Code Intelligence & Deployment Evidence (GitHub) */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Code Intelligence & Deployment Evidence (GitHub)
            </h3>
          </div>
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
            Version Control Intelligence
          </span>
        </div>

        {/* GitHub Source Investigation & Code Context */}
        {incident.githubSourceEvidence && incident.githubSourceEvidence.status !== 'NO_STACK_TRACE' && (
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                  Source Correlation & Code Context
                </h4>
              </div>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full border flex items-center gap-1 font-medium ${
                  incident.githubSourceEvidence.status === 'MATCHED'
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60'
                    : incident.githubSourceEvidence.status === 'FILE_NOT_FOUND'
                    ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-900/60'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                }`}
              >
                {incident.githubSourceEvidence.status === 'MATCHED' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
                {incident.githubSourceEvidence.status === 'FILE_NOT_FOUND' && <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />}
                <span>
                  {incident.githubSourceEvidence.status === 'MATCHED'
                    ? 'Source location verified'
                    : incident.githubSourceEvidence.status === 'FILE_NOT_FOUND'
                    ? 'File not found at commit'
                    : incident.githubSourceEvidence.status === 'NO_COMMIT'
                    ? 'Deployment commit required'
                    : incident.githubSourceEvidence.status}
                </span>
              </span>
            </div>

            {/* Location & Commit Metadata */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
              <div className="bg-white dark:bg-slate-800 p-2.5 rounded-md border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-medium">Source File</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-semibold truncate block mt-0.5" title={incident.githubSourceEvidence.file_path || 'None'}>
                  {incident.githubSourceEvidence.file_path || 'None'}
                </span>
              </div>
              <div className="bg-white dark:bg-slate-800 p-2.5 rounded-md border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-medium">Target Line</span>
                <span className="text-red-600 dark:text-red-400 font-semibold block mt-0.5 font-mono">
                  Line {incident.githubSourceEvidence.target_line || incident.githubSourceEvidence.location?.line_number || 'N/A'}
                  {incident.githubSourceEvidence.location?.function_name ? ` (in ${incident.githubSourceEvidence.location.function_name})` : ''}
                </span>
              </div>
              <div className="bg-white dark:bg-slate-800 p-2.5 rounded-md border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] text-slate-500 dark:text-slate-400 block uppercase font-medium">Deployment Commit</span>
                <span className="font-mono text-blue-600 dark:text-blue-400 font-semibold block mt-0.5 truncate" title={incident.githubSourceEvidence.deployment_commit || 'None'}>
                  {incident.githubSourceEvidence.deployment_commit ? incident.githubSourceEvidence.deployment_commit.slice(0, 7) : (incident.deployedCommit ? incident.deployedCommit.slice(0, 7) : 'None')}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-300 italic">
              {incident.githubSourceEvidence.message}
            </p>

            {/* Surrounding Code Window */}
            {incident.githubSourceEvidence.source_lines && incident.githubSourceEvidence.source_lines.length > 0 && (
              <div className="mt-2 space-y-1">
                <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pb-1">
                  <span>Source Context (Commit {incident.githubSourceEvidence.deployment_commit?.slice(0, 7) || 'HEAD'})</span>
                  <span className="font-mono">{incident.githubSourceEvidence.file_path}</span>
                </div>
                <div className="bg-slate-900 dark:bg-slate-950 rounded-md border border-slate-800 overflow-x-auto p-3 font-mono text-xs text-slate-200">
                  {incident.githubSourceEvidence.source_lines.map((sl) => (
                    <div
                      key={sl.line_number}
                      className={`flex items-center px-2 py-0.5 rounded ${
                        sl.is_target
                          ? 'bg-red-900/40 text-red-200 font-semibold border-l-2 border-red-500'
                          : 'text-slate-400 hover:bg-slate-800/40'
                      }`}
                    >
                      <span className="w-10 shrink-0 text-right pr-3 select-none text-[11px] text-slate-500">
                        {sl.line_number}
                      </span>
                      <pre className="overflow-x-auto whitespace-pre font-mono text-[11px]">
                        {sl.content}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {incident.githubCommits && incident.githubCommits.length > 0 ? (
          <div className="space-y-4">
            {incident.githubCommits.map((commit) => (
              <GitHubCommitCard
                key={commit.sha}
                commit={commit}
                rootCauseCandidates={incident.rootCauseCandidates}
              />
            ))}
          </div>
        ) : (
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-6 text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center mx-auto text-slate-400">
              <GitCommit className="w-4 h-4" />
            </div>
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
              No deployment commit hash is associated with this incident.
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              When deployments cite a Git commit SHA, IntelliIncident retrieves commit metadata, modified files, and diff statistics to correlate code changes with runtime telemetry.
            </p>
          </div>
        )}
      </div>

      {/* Sentry Runtime Error Evidence */}
      {incident.sentryEvidence && (
        <SentryEvidenceCard
          evidence={incident.sentryEvidence}
          rootCauseCandidates={incident.rootCauseCandidates}
        />
      )}

      {/* Prometheus Metric Telemetry Evidence */}
      {(incident.prometheusEvidence || incident.prometheus_evidence) && (
        <PrometheusEvidenceCard
          evidence={(incident.prometheusEvidence || incident.prometheus_evidence)!}
          rootCauseCandidates={incident.rootCauseCandidates}
        />
      )}

      {/* Jira Work Item & Ticket Evidence */}
      {(incident.jiraEvidence || incident.jira_evidence) && (
        <JiraEvidenceCard
          evidence={(incident.jiraEvidence || incident.jira_evidence)!}
          rootCauseCandidates={incident.rootCauseCandidates}
        />
      )}

      {/* SECTION 3: ML Analysis */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Machine Learning Inference Analysis
            </h3>
          </div>
          <span className="text-xs font-medium text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 px-2.5 py-0.5 rounded-full border border-purple-200 dark:border-purple-800/60">
            ML Models Active
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Anomaly Detection (Isolation Forest) */}
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
                  Anomaly Detection
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  Model: {mlAnalysis.anomaly.model}
                </span>
              </div>
              <span
                className={`text-xs font-medium px-2.5 py-0.5 rounded-full border ${
                  mlAnalysis.anomaly.detected
                    ? 'bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-900/60'
                    : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60'
                }`}
              >
                {mlAnalysis.anomaly.detected ? 'Anomaly Detected' : 'Normal'}
              </span>
            </div>

            <div className="p-3 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Anomaly Score:</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-bold">
                  {(mlAnalysis.anomaly.score).toFixed(2)} / 1.00
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Decision Threshold:</span>
                <span className="font-mono text-slate-600 dark:text-slate-300">{mlAnalysis.anomaly.threshold}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Observed Deviation:</span>
                <span className="text-amber-700 dark:text-amber-300 font-medium">{mlAnalysis.anomaly.observedDeviation}</span>
              </div>
            </div>

            <div>
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1.5">
                Features Analyzed:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {mlAnalysis.anomaly.featuresAnalyzed.map((feat) => (
                  <span
                    key={feat}
                    className="text-[11px] bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 font-mono"
                  >
                    {feat}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Severity Prediction (Random Forest) */}
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
                  Severity Prediction
                </span>
                <span className="text-[11px] text-slate-500 dark:text-slate-400">
                  Model: {mlAnalysis.severityPrediction.model}
                </span>
              </div>
              <SeverityBadge severity={mlAnalysis.severityPrediction.predictedSeverity} />
            </div>

            <div className="text-xs space-y-2.5">
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                Class Probabilities:
              </span>

              {/* Class Probability bars */}
              {(
                [
                  { label: 'Low', val: mlAnalysis.severityPrediction.classProbabilities.low, color: 'bg-blue-600' },
                  { label: 'Medium', val: mlAnalysis.severityPrediction.classProbabilities.medium, color: 'bg-amber-500' },
                  { label: 'High', val: mlAnalysis.severityPrediction.classProbabilities.high, color: 'bg-orange-500' },
                  { label: 'Critical', val: mlAnalysis.severityPrediction.classProbabilities.critical, color: 'bg-red-600' },
                ] as const
              ).map((cls) => (
                <div key={cls.label}>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-slate-600 dark:text-slate-400 font-medium">{cls.label}</span>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">
                      {Math.round(cls.val * 100)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${cls.color}`}
                      style={{ width: `${Math.round(cls.val * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 4: Fuzzy Risk Assessment */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Mamdani Fuzzy Risk Assessment
            </h3>
          </div>
          <span className="text-xs font-medium text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 px-2.5 py-0.5 rounded-full border border-amber-200 dark:border-amber-800/60">
            Centroid Defuzzification
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Inputs & Linguistic states */}
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 space-y-3">
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
              Linguistic Antecedents
            </span>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Error Rate:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {metrics.errorRate}%{' '}
                  <span className="text-red-600 dark:text-red-400 text-[11px]">
                    ({fuzzyRisk.inputs.errorRateState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">User Impact:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {metrics.affectedUsers.toLocaleString()}{' '}
                  <span className="text-red-600 dark:text-red-400 text-[11px]">
                    ({fuzzyRisk.inputs.userImpactState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Latency:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {metrics.latencyP99}ms{' '}
                  <span className="text-amber-700 dark:text-amber-300 text-[11px]">
                    ({fuzzyRisk.inputs.latencyState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-200 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Deployment Recency:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {metrics.deploymentRecencyMinutes}m{' '}
                  <span className="text-blue-600 dark:text-blue-400 text-[11px]">
                    ({fuzzyRisk.inputs.deploymentRecencyState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-500 dark:text-slate-400">Service Criticality:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  Tier-1{' '}
                  <span className="text-red-600 dark:text-red-400 text-[11px]">
                    ({fuzzyRisk.inputs.serviceCriticalityState})
                  </span>
                </span>
              </div>
            </div>
          </div>

          {/* Risk Score & Level Output */}
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
                  Composite Risk Output
                </span>
                <span className="text-[10px] text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800/60 font-medium">
                  Verified
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-red-600 dark:text-red-400 font-mono">
                  {fuzzyRisk.riskScore}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">/ 100</span>
              </div>
              <div className="mt-2">
                <RiskBadge risk={fuzzyRisk.riskLevel} />
              </div>
              <p className="mt-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Evaluated from operational telemetry using the 28-rule Mamdani fuzzy inference system.
              </p>
            </div>

            <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-700 text-[11px] text-slate-500 dark:text-slate-400">
              Soft Computing &bull; Centroid Defuzzification
            </div>
          </div>

          {/* Triggered Fuzzy Rules */}
          <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 space-y-2">
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block">
              Dominant Heuristic Rules
            </span>
            <div className="space-y-2 text-xs">
              {fuzzyRisk.triggeredRules.map((rule) => (
                <div
                  key={rule.id}
                  className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-2.5 space-y-1"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-amber-800 dark:text-amber-300 font-semibold">{rule.id}</span>
                    <span className="text-[10px] text-slate-400 dark:text-slate-400">
                      Strength: {rule.weight}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-700 dark:text-slate-300 leading-snug">
                    {rule.ruleText}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 5: Evidence Timeline */}
      <EvidenceTimeline events={incident.evidenceTimeline} />

      {/* SECTION 6: Root Cause Analysis */}
      <RootCauseList candidates={incident.rootCauseCandidates} />

      {/* SECTION 7: Recommendations */}
      <RecommendationsList recommendations={incident.recommendations} />
    </div>
  );
};
