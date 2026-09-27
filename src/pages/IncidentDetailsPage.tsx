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
      <div className="py-20 text-center font-mono text-sm text-slate-400">
        Loading incident investigation workspace...
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="py-20 text-center font-mono text-sm text-rose-400">
        Incident {id} not found.
      </div>
    );
  }

  const { metrics, mlAnalysis, fuzzyRisk } = incident;

  return (
    <div className="space-y-6">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <button
          type="button"
          onClick={() => navigate('/incidents')}
          className="flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Incidents</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate('/investigation')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 text-xs font-mono font-medium transition-colors cursor-pointer"
          >
            <SearchCode className="w-3.5 h-3.5" />
            <span>Open in Investigation Workspace</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/reports')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-mono transition-colors cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Incident Report</span>
          </button>
        </div>
      </div>

      {/* Incident Header */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-xl font-bold font-mono text-teal-400">{incident.id}</span>
              <SeverityBadge severity={incident.severity} />
              <RiskBadge risk={incident.risk} score={incident.riskScore} showScore />
              <StatusBadge status={incident.status} />
            </div>
            <h2 className="text-lg font-semibold text-slate-100 font-sans">{incident.title}</h2>
            <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
              {incident.summary}
            </p>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 p-3.5 rounded-md text-xs font-mono space-y-1.5 shrink-0 min-w-[240px]">
            <div className="flex justify-between text-slate-400">
              <span>Service:</span>
              <span className="text-slate-200 font-semibold">{incident.service}</span>
            </div>
            {incident.projectId && (
              <div className="flex justify-between text-slate-400">
                <span>Project:</span>
                <span className="text-teal-400 font-semibold">{incident.projectId}</span>
              </div>
            )}
            {incident.environmentId && (
              <div className="flex justify-between text-slate-400">
                <span>Environment:</span>
                <span className="text-cyan-400 font-semibold">{incident.environmentName || incident.environmentId}</span>
              </div>
            )}
            {incident.deployedCommit && (
              <div className="flex justify-between text-slate-400">
                <span>Deployed Commit:</span>
                <span className="text-cyan-400 font-semibold font-mono">{incident.deployedCommit.slice(0, 7)}</span>
              </div>
            )}
            <div className="flex justify-between text-slate-400">
              <span>Timestamp:</span>
              <span className="text-slate-200">{incident.timestamp.substring(0, 16).replace('T', ' ')} UTC</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Anomaly Status:</span>
              <span className={incident.anomalyDetected ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                {incident.anomalyDetected ? 'ANOMALY DETECTED' : 'NORMAL'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 1: Incident Overview */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-400" />
            <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
              Section 1: Incident Overview & Operational Telemetry
            </h3>
          </div>
          <span className="text-[11px] font-mono text-slate-400">Metrics Snapshot</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono">
          <div className="bg-slate-950/70 border border-slate-800/90 rounded p-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Service</span>
            <span className="text-sm font-bold text-slate-200 mt-1 block truncate">
              {metrics.service}
            </span>
            {incident.environmentId && (
              <span className="text-[10px] text-cyan-400 mt-0.5 block truncate">
                Env: {incident.environmentId}
              </span>
            )}
          </div>

          <div className="bg-slate-950/70 border border-slate-800/90 rounded p-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
              Affected Users
            </span>
            <span className="text-sm font-bold text-rose-400 mt-1 block">
              {metrics.affectedUsers.toLocaleString()}
            </span>
          </div>

          <div className="bg-slate-950/70 border border-slate-800/90 rounded p-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
              Error Rate
            </span>
            <span className="text-sm font-bold text-rose-400 mt-1 block">
              {metrics.errorRate}%
            </span>
          </div>

          <div className="bg-slate-950/70 border border-slate-800/90 rounded p-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
              P99 Latency
            </span>
            <span className="text-sm font-bold text-amber-400 mt-1 block">
              {metrics.latencyP99}ms
            </span>
          </div>

          <div className="bg-slate-950/70 border border-slate-800/90 rounded p-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
              Request Volume
            </span>
            <span className="text-sm font-bold text-slate-200 mt-1 block">
              {metrics.requestVolume.toLocaleString()} req/s
            </span>
          </div>

          <div className="bg-slate-950/70 border border-slate-800/90 rounded p-3">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
              Deployment Recency
            </span>
            <span className="text-sm font-bold text-cyan-400 mt-1 block">
              {metrics.deploymentRecencyMinutes}m ago
            </span>
          </div>
        </div>
      </div>

      {/* SECTION 2: Code Intelligence & Deployment Evidence (GitHub) */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-teal-400" />
            <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
              Section 2: Code Intelligence & Deployment Evidence (GitHub)
            </h3>
          </div>
          <span className="text-xs font-mono text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/30">
            Source Control Intelligence
          </span>
        </div>

        {/* GitHub Source Investigation & Code Context */}
        {incident.githubSourceEvidence && incident.githubSourceEvidence.status !== 'NO_STACK_TRACE' && (
          <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-cyan-400" />
                <h4 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider">
                  GitHub Source Correlation & Code Context
                </h4>
              </div>
              <span
                className={`text-[11px] font-mono px-2 py-0.5 rounded border flex items-center gap-1 ${
                  incident.githubSourceEvidence.status === 'MATCHED'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : incident.githubSourceEvidence.status === 'FILE_NOT_FOUND'
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {incident.githubSourceEvidence.status === 'MATCHED' && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                {incident.githubSourceEvidence.status === 'FILE_NOT_FOUND' && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                <span>
                  {incident.githubSourceEvidence.status === 'MATCHED'
                    ? '✓ Source location matched'
                    : incident.githubSourceEvidence.status === 'FILE_NOT_FOUND'
                    ? 'File not found at commit'
                    : incident.githubSourceEvidence.status === 'NO_COMMIT'
                    ? 'Deployment commit required'
                    : incident.githubSourceEvidence.status}
                </span>
              </span>
            </div>

            {/* Location & Commit Metadata */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
              <div className="bg-slate-900/80 p-2 rounded border border-slate-800/80">
                <span className="text-[10px] text-slate-400 block uppercase">Source File</span>
                <span className="text-cyan-300 font-semibold truncate block mt-0.5" title={incident.githubSourceEvidence.file_path || 'None'}>
                  {incident.githubSourceEvidence.file_path || 'None'}
                </span>
              </div>
              <div className="bg-slate-900/80 p-2 rounded border border-slate-800/80">
                <span className="text-[10px] text-slate-400 block uppercase">Target Line</span>
                <span className="text-rose-400 font-semibold block mt-0.5">
                  Line {incident.githubSourceEvidence.target_line || incident.githubSourceEvidence.location?.line_number || 'N/A'}
                  {incident.githubSourceEvidence.location?.function_name ? ` (in ${incident.githubSourceEvidence.location.function_name})` : ''}
                </span>
              </div>
              <div className="bg-slate-900/80 p-2 rounded border border-slate-800/80">
                <span className="text-[10px] text-slate-400 block uppercase">Deployment Commit</span>
                <span className="text-teal-400 font-semibold block mt-0.5 truncate" title={incident.githubSourceEvidence.deployment_commit || 'None'}>
                  {incident.githubSourceEvidence.deployment_commit ? incident.githubSourceEvidence.deployment_commit.slice(0, 7) : (incident.deployedCommit ? incident.deployedCommit.slice(0, 7) : 'None')}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-300 font-sans italic">
              {incident.githubSourceEvidence.message}
            </p>

            {/* Surrounding Code Window */}
            {incident.githubSourceEvidence.source_lines && incident.githubSourceEvidence.source_lines.length > 0 && (
              <div className="mt-2 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pb-1">
                  <span>Source Context (Commit {incident.githubSourceEvidence.deployment_commit?.slice(0, 7) || 'HEAD'})</span>
                  <span className="text-slate-500">{incident.githubSourceEvidence.file_path}</span>
                </div>
                <div className="bg-slate-950 rounded border border-slate-800 overflow-x-auto p-2 font-mono text-xs">
                  {incident.githubSourceEvidence.source_lines.map((sl) => (
                    <div
                      key={sl.line_number}
                      className={`flex items-center px-2 py-0.5 rounded ${
                        sl.is_target
                          ? 'bg-rose-950/50 text-rose-300 font-semibold border-l-2 border-rose-500'
                          : 'text-slate-400 hover:bg-slate-900/40'
                      }`}
                    >
                      <span className="w-10 shrink-0 text-right pr-3 select-none text-[11px] text-slate-600">
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
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-6 text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
              <GitCommit className="w-4 h-4" />
            </div>
            <p className="text-xs font-mono text-slate-400">
              No deployment commit hash is associated with this incident.
            </p>
            <p className="text-[11px] font-sans text-slate-500 max-w-md mx-auto">
              When deployments cite a valid Git commit SHA, IntelliIncident retrieves commit metadata, modified files, and diff statistics to correlate code changes with runtime evidence.
            </p>
          </div>
        )}
      </div>

      {/* SECTION 3: ML Analysis */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
              Section 3: Machine Learning Inference Analysis
            </h3>
          </div>
          <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/30">
            Inference Status: Active
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Anomaly Detection (Isolation Forest) */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono font-semibold text-slate-200 block">
                  Anomaly Detection
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Model: {mlAnalysis.anomaly.model}
                </span>
              </div>
              <span
                className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                  mlAnalysis.anomaly.detected
                    ? 'bg-rose-500/15 text-rose-400 border-rose-500/40'
                    : 'bg-teal-500/15 text-teal-400 border-teal-500/40'
                }`}
              >
                {mlAnalysis.anomaly.detected ? 'DETECTED' : 'NORMAL'}
              </span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded border border-slate-800/80 space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Anomaly Score:</span>
                <span className="text-slate-200 font-bold">
                  {(mlAnalysis.anomaly.score).toFixed(2)} / 1.00
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Decision Threshold:</span>
                <span className="text-slate-400">{mlAnalysis.anomaly.threshold}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Statistical Shift:</span>
                <span className="text-amber-400">{mlAnalysis.anomaly.observedDeviation}</span>
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                Features Analyzed:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {mlAnalysis.anomaly.featuresAnalyzed.map((feat) => (
                  <span
                    key={feat}
                    className="text-[10px] font-mono bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800"
                  >
                    {feat}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Severity Prediction (Random Forest) */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono font-semibold text-slate-200 block">
                  Severity Prediction
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Model: {mlAnalysis.severityPrediction.model}
                </span>
              </div>
              <SeverityBadge severity={mlAnalysis.severityPrediction.predictedSeverity} />
            </div>

            <div className="text-xs font-mono space-y-2.5">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                Class Probabilities:
              </span>

              {/* Class Probability bars */}
              {(
                [
                  { label: 'Low', val: mlAnalysis.severityPrediction.classProbabilities.low, color: 'bg-blue-500' },
                  { label: 'Medium', val: mlAnalysis.severityPrediction.classProbabilities.medium, color: 'bg-amber-500' },
                  { label: 'High', val: mlAnalysis.severityPrediction.classProbabilities.high, color: 'bg-orange-500' },
                  { label: 'Critical', val: mlAnalysis.severityPrediction.classProbabilities.critical, color: 'bg-rose-500' },
                ] as const
              ).map((cls) => (
                <div key={cls.label}>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-slate-400">{cls.label}</span>
                    <span className="font-semibold text-slate-200">
                      {Math.round(cls.val * 100)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
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
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
              Section 4: Mamdani Fuzzy Risk Assessment
            </h3>
          </div>
          <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
            Mamdani COA Defuzzification
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Inputs & Linguistic states */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-3">
            <span className="text-xs font-mono font-semibold text-slate-200 block">
              Fuzzy Linguistic Inputs
            </span>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">Error Rate:</span>
                <span className="font-semibold text-slate-200">
                  {metrics.errorRate}%{' '}
                  <span className="text-rose-400 text-[10px]">
                    ({fuzzyRisk.inputs.errorRateState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">User Impact:</span>
                <span className="font-semibold text-slate-200">
                  {metrics.affectedUsers.toLocaleString()}{' '}
                  <span className="text-rose-400 text-[10px]">
                    ({fuzzyRisk.inputs.userImpactState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">Latency:</span>
                <span className="font-semibold text-slate-200">
                  {metrics.latencyP99}ms{' '}
                  <span className="text-amber-400 text-[10px]">
                    ({fuzzyRisk.inputs.latencyState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-slate-900">
                <span className="text-slate-400">Deployment Recency:</span>
                <span className="font-semibold text-slate-200">
                  {metrics.deploymentRecencyMinutes}m{' '}
                  <span className="text-cyan-400 text-[10px]">
                    ({fuzzyRisk.inputs.deploymentRecencyState})
                  </span>
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-slate-400">Service Criticality:</span>
                <span className="font-semibold text-slate-200">
                  Tier-1{' '}
                  <span className="text-rose-400 text-[10px]">
                    ({fuzzyRisk.inputs.serviceCriticalityState})
                  </span>
                </span>
              </div>
            </div>
          </div>

          {/* Risk Score & Level Output */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-semibold text-slate-200 block">
                  Fuzzy Risk Assessment
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 font-semibold">
                  System Generated (Read-Only)
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold font-mono text-rose-400">
                  {fuzzyRisk.riskScore}
                </span>
                <span className="text-xs font-mono text-slate-400">/ 100</span>
              </div>
              <div className="mt-2">
                <RiskBadge risk={fuzzyRisk.riskLevel} />
              </div>
              <p className="mt-3 text-xs text-slate-400 font-sans leading-relaxed">
                Calculated automatically from incident telemetry using the Mamdani fuzzy inference engine.
              </p>
            </div>

            <div className="mt-3 pt-2 border-t border-slate-900 text-[10px] font-mono text-slate-400">
              Soft Computing &bull; 28 Mamdani Rules &bull; Centroid Defuzzification
            </div>
          </div>

          {/* Triggered Fuzzy Rules */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-2">
            <span className="text-xs font-mono font-semibold text-slate-200 block">
              Active Triggered Fuzzy Rules
            </span>
            <div className="space-y-2 font-mono text-xs">
              {fuzzyRisk.triggeredRules.map((rule) => (
                <div
                  key={rule.id}
                  className="bg-slate-900/60 border border-slate-800/80 rounded p-2.5 space-y-1"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-amber-400 font-semibold">{rule.id}</span>
                    <span className="text-[10px] text-slate-400">
                      Strength: {rule.weight}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-200 leading-snug font-mono">
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
