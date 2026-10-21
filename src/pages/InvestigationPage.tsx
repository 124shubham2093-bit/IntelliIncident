import React, { useEffect, useState } from 'react';
import {
  ArrowDown,
  GitCommit,
  AlertOctagon,
  BellRing,
  MessageSquareWarning,
  Layers,
} from 'lucide-react';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { EvidenceTimeline } from '@/components/Incident/EvidenceTimeline';
import { RootCauseList } from '@/components/Incident/RootCauseList';
import { SentryEvidenceCard } from '@/components/Incident/SentryEvidenceCard';
import { PrometheusEvidenceCard } from '@/components/Incident/PrometheusEvidenceCard';
import { JiraEvidenceCard } from '@/components/Incident/JiraEvidenceCard';
import { getIncidents, getIncidentById } from '@/api/incidents';
import { Incident, IncidentDetails } from '@/types';

export const InvestigationPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [incidentDetail, setIncidentDetail] = useState<IncidentDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadIncidents() {
      setLoading(true);
      const res = await getIncidents();
      setIncidents(res.data);
      if (res.data.length > 0) {
        setSelectedId(res.data[0].id);
      } else {
        setSelectedId('');
        setIncidentDetail(null);
        setLoading(false);
      }
    }
    loadIncidents();
  }, []);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedId) {
        setIncidentDetail(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      const res = await getIncidentById(selectedId);
      setIncidentDetail(res.data);
      setLoading(false);
    }
    loadDetail();
  }, [selectedId]);

  return (
    <div className="space-y-6">
      {/* Header & Incident Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-sans">
            Investigation Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-source correlation and causal inference analysis
          </p>
        </div>

        {/* Incident Selector Dropdown */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-600 font-medium uppercase tracking-wider shrink-0">
            Target Incident:
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            disabled={incidents.length === 0}
            aria-label="Target Incident"
            className="bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-700 font-medium focus:outline-none focus:border-blue-500 disabled:opacity-50 cursor-pointer shadow-xs"
          >
            {incidents.length === 0 ? (
              <option value="">No incidents available</option>
            ) : (
              incidents.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.id} — {inc.service} ({inc.severity})
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500 font-sans">
          Correlating operational signals and causal evidence for {selectedId || 'incident'}...
        </div>
      ) : incidents.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-12 text-center max-w-xl mx-auto space-y-4 my-8 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
            <Layers className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-800">No Incidents Available for Investigation</h3>
            <p className="text-xs text-slate-500 leading-relaxed font-sans">
              The system database is currently operating in real-data mode with no incidents recorded.
              Ingest telemetry to inspect causal inference, timeline events, and automated root cause analysis.
            </p>
          </div>
        </div>
      ) : incidentDetail && (
        <>
          {/* Active Context Banner */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold font-mono text-blue-600">
                {incidentDetail.id}
              </span>
              <span className="text-sm font-semibold text-slate-900">
                {incidentDetail.title}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <SeverityBadge severity={incidentDetail.severity} size="sm" />
              <RiskBadge
                risk={incidentDetail.risk}
                score={incidentDetail.riskScore}
                showScore
              />
            </div>
          </div>

          {/* Automated Fuzzy Risk Assessment */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Fuzzy Risk Assessment
                </span>
                <span className="text-slate-300">&bull;</span>
                <span className="text-xs text-slate-600">
                  Risk Score:{' '}
                  <span className="text-red-600 font-bold font-mono">
                    {incidentDetail.riskScore} / 100
                  </span>
                </span>
                <span className="text-slate-300">&bull;</span>
                <span className="text-xs text-slate-600 flex items-center gap-1.5">
                  Level:
                  <RiskBadge risk={incidentDetail.risk} />
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Calculated automatically from incident telemetry using the 28-rule Mamdani fuzzy inference system.
              </p>
            </div>
            <div className="text-xs text-slate-500 shrink-0 bg-slate-50 px-3 py-1 rounded-md border border-slate-200">
              Mamdani FIS &bull; Centroid Defuzzification
            </div>
          </div>

          {/* VISUAL CAUSAL PIPELINE:
              Operational Signals -> Evidence Correlation -> Root Cause Candidates */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Causal Inference Pipeline
                </h3>
              </div>
              <span className="text-xs text-slate-500">
                Multi-Source Evidence
              </span>
            </div>

            {/* Pipeline Stage 1: Operational Signals */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 flex items-start gap-2.5">
                <GitCommit className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div className="min-w-0 flex-1">
                  <span className="text-xs font-semibold text-slate-900 block">
                    Deployment Events
                  </span>
                  {incidentDetail.githubCommits && incidentDetail.githubCommits.length > 0 ? (
                    <div className="mt-1 space-y-0.5">
                      <div className="flex items-center gap-1.5 font-mono text-xs">
                        <span className="text-blue-700 font-semibold">
                          {incidentDetail.githubCommits[0].short_sha || incidentDetail.githubCommits[0].sha.slice(0, 7)}
                        </span>
                        <span className="text-slate-500 truncate">
                          by {incidentDetail.githubCommits[0].author.name}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 truncate" title={incidentDetail.githubCommits[0].message}>
                        {incidentDetail.githubCommits[0].message.split('\n')[0]}
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 mt-0.5">
                      CI/CD commits, image hashes, config drift
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 flex items-start gap-2.5">
                <AlertOctagon className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-semibold text-slate-900 block">
                      Runtime Errors
                    </span>
                    {incidentDetail.sentryEvidence && incidentDetail.sentryEvidence.status === 'CONNECTED' && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200 font-medium">
                        Sentry
                      </span>
                    )}
                  </div>
                  {incidentDetail.sentryEvidence && incidentDetail.sentryEvidence.status === 'CONNECTED' ? (
                    <div className="mt-1 space-y-0.5">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-red-700 font-semibold truncate font-mono">
                          {incidentDetail.sentryEvidence.matched_exception_type || `${incidentDetail.sentryEvidence.issue_count} issue(s)`}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 truncate" title={incidentDetail.sentryEvidence.message}>
                        {incidentDetail.sentryEvidence.message}
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 mt-0.5">
                      HTTP 5xx spikes, exception stack traces
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 flex items-start gap-2.5">
                <BellRing className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-semibold text-slate-900 block">
                      Metric Telemetry
                    </span>
                    {(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence)?.status === 'CONNECTED' && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-medium">
                        Prometheus
                      </span>
                    )}
                  </div>
                  {(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence) ? (
                    <div className="mt-1 space-y-0.5">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-amber-800 font-semibold truncate">
                          {(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence)!.anomalies_detected} Anomalies
                        </span>
                        <span className="text-slate-400">&bull;</span>
                        <span className="text-slate-600 truncate">
                          Correlation: {(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence)!.highest_correlation}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 truncate" title={(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence)!.summary}>
                        {(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence)!.summary}
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 mt-0.5">
                      Latency shifts, connection pools, CPU
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 flex items-start gap-2.5">
                <MessageSquareWarning className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-semibold text-slate-900 block">
                      Work Items
                    </span>
                    {(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)?.status === 'CONNECTED' && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                        Jira
                      </span>
                    )}
                  </div>
                  {(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)?.primary_issue ? (
                    <div className="mt-1 space-y-0.5">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-blue-700 font-semibold font-mono truncate">
                          {(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)!.primary_issue!.key}
                        </span>
                        <span className="text-slate-400">&bull;</span>
                        <span className="text-slate-700 truncate">
                          {(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)!.primary_issue!.summary}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 truncate" title={(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)!.summary}>
                        {(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)!.summary}
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 mt-0.5">
                      Correlated bug tickets & issue history
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Pipeline Stage 2: Evidence Correlation Engine */}
            <div className="flex justify-center my-2">
              <div className="flex items-center gap-1 text-slate-400 text-xs font-medium">
                <ArrowDown className="w-4 h-4 text-blue-600 animate-bounce" />
                <span>Evidence Correlation</span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200 mb-3">
                <span className="text-xs font-semibold text-slate-800 uppercase tracking-wider">
                  Correlated Diagnostic Indicators
                </span>
                <span className="text-xs text-slate-500">
                  {incidentDetail.evidenceTimeline.length} Evidence Events Extracted
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs">
                {incidentDetail.evidenceTimeline.slice(0, 4).map((ev) => (
                  <div
                    key={ev.id}
                    className="bg-white border border-slate-200 rounded-md p-2.5 space-y-1 shadow-2xs"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-slate-900">{ev.service}</span>
                      <span className="text-slate-400 font-mono">{ev.timestamp.substring(11, 16)} UTC</span>
                    </div>
                    <p className="text-slate-600 line-clamp-2 leading-relaxed">{ev.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Pipeline Stage 3: Root Cause Deduction */}
            <div className="flex justify-center my-2">
              <div className="flex items-center gap-1 text-slate-400 text-xs font-medium">
                <ArrowDown className="w-4 h-4 text-blue-600 animate-bounce" />
                <span>Root Cause Inference Engine</span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-800 uppercase tracking-wider block mb-2">
                Deduction Output
              </span>
              <p className="text-xs text-slate-700 leading-relaxed">
                Aggregated signals mapped to {incidentDetail.rootCauseCandidates.length} candidate root causes.
                Top match:{' '}
                <strong className="text-slate-900">
                  {incidentDetail.rootCauseCandidates[0]?.candidate || 'Under Analysis'}
                </strong>{' '}
                with{' '}
                <strong className="text-blue-700">
                  {Math.round((incidentDetail.rootCauseCandidates[0]?.score || 0) * 100)}%
                </strong>{' '}
                confidence based on multi-source cross-verification.
              </p>
            </div>
          </div>

          {/* Sentry Runtime Error Evidence */}
          {incidentDetail.sentryEvidence && (
            <SentryEvidenceCard
              evidence={incidentDetail.sentryEvidence}
              rootCauseCandidates={incidentDetail.rootCauseCandidates}
            />
          )}

          {/* Prometheus Metric Telemetry Evidence */}
          {(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence) && (
            <PrometheusEvidenceCard
              evidence={(incidentDetail.prometheusEvidence || incidentDetail.prometheus_evidence)!}
              rootCauseCandidates={incidentDetail.rootCauseCandidates}
            />
          )}

          {/* Jira Work Item Evidence */}
          {(incidentDetail.jiraEvidence || incidentDetail.jira_evidence) && (
            <JiraEvidenceCard
              evidence={(incidentDetail.jiraEvidence || incidentDetail.jira_evidence)!}
              rootCauseCandidates={incidentDetail.rootCauseCandidates}
            />
          )}

          {/* Chronological Evidence Timeline */}
          <EvidenceTimeline
            events={incidentDetail.evidenceTimeline}
            title="Evidence Timeline"
            subtitle="Chronological sequence of all correlated events"
          />

          {/* Ranked Root Cause Candidates */}
          <RootCauseList candidates={incidentDetail.rootCauseCandidates} />
        </>
      )}
    </div>
  );
};
