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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
            Investigation Workspace
          </h1>
        </div>

        {/* Incident Selector Dropdown */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-mono text-slate-400 uppercase tracking-wider shrink-0">
            Target Incident:
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            disabled={incidents.length === 0}
            className="bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs font-mono text-teal-300 font-semibold focus:outline-none focus:border-teal-500 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
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
        <div className="py-16 text-center font-mono text-xs text-slate-400">
          Correlating operational signals and causal evidence for {selectedId || 'incident'}...
        </div>
      ) : incidents.length === 0 ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-12 text-center max-w-xl mx-auto space-y-4 my-8">
          <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center mx-auto text-slate-400">
            <Layers className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-200">No Incidents Available for Investigation</h3>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              The system database is currently operating in real-data mode with no incidents recorded.
              Ingest telemetry or submit an incident via <code className="text-teal-400 font-mono">POST /api/incidents</code> to inspect causal inference, timeline events, and automated root cause analysis.
            </p>
          </div>
        </div>
      ) : incidentDetail && (
        <>
          {/* Active Context Banner */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-base font-bold font-mono text-teal-400">
                {incidentDetail.id}
              </span>
              <span className="text-sm font-sans font-medium text-slate-200">
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
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-semibold text-slate-100 uppercase tracking-wider">
                  Fuzzy Risk Assessment
                </span>
                <span className="text-slate-600">&bull;</span>
                <span className="text-xs text-slate-300">
                  Risk Score:{' '}
                  <span className="text-rose-400 font-bold">
                    {incidentDetail.riskScore}
                  </span>
                </span>
                <span className="text-slate-600">&bull;</span>
                <span className="text-xs text-slate-300 flex items-center gap-1.5">
                  Risk Level:
                  <RiskBadge risk={incidentDetail.risk} />
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Calculated automatically from incident telemetry using the Mamdani fuzzy inference engine.
              </p>
            </div>
            <div className="text-[10px] text-slate-500 font-mono shrink-0 bg-slate-950/80 px-2.5 py-1 rounded border border-slate-800">
              Mamdani FIS &bull; Centroid Defuzzification &bull; Read-Only
            </div>
          </div>

          {/* VISUAL CAUSAL PIPELINE:
              Operational Signals -> Evidence Correlation -> Root Cause Candidates */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                  Causal Inference Pipeline Architecture
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                Dataflow Hierarchy
              </span>
            </div>

            {/* Pipeline Stage 1: Operational Signals */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="bg-slate-950/80 border border-slate-800 rounded p-3 flex items-start gap-2.5">
                <GitCommit className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div className="min-w-0 flex-1">
                  <span className="text-xs font-mono font-semibold text-slate-200 block">
                    Deployment Events
                  </span>
                  {incidentDetail.githubCommits && incidentDetail.githubCommits.length > 0 ? (
                    <div className="mt-1 space-y-0.5">
                      <div className="flex items-center gap-1.5 font-mono text-[11px]">
                        <span className="text-cyan-400 font-semibold">
                          {incidentDetail.githubCommits[0].short_sha || incidentDetail.githubCommits[0].sha.slice(0, 7)}
                        </span>
                        <span className="text-slate-400 truncate">
                          by {incidentDetail.githubCommits[0].author.name}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate" title={incidentDetail.githubCommits[0].message}>
                        {incidentDetail.githubCommits[0].message.split('\n')[0]}
                      </p>
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      CI/CD commits, image hashes, config drift
                    </p>
                  )}
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded p-3 flex items-start gap-2.5">
                <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-mono font-semibold text-slate-200 block">
                    Runtime Errors
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    HTTP 5xx spikes, exception stack traces
                  </p>
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded p-3 flex items-start gap-2.5">
                <BellRing className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-mono font-semibold text-slate-200 block">
                    Monitoring Signals
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    P99 latency shifts, connection pools, CPU
                  </p>
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800 rounded p-3 flex items-start gap-2.5">
                <MessageSquareWarning className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-mono font-semibold text-slate-200 block">
                    Support Tickets
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Customer failure reports, webhook velocity
                  </p>
                </div>
              </div>
            </div>

            {/* Downward Transition indicator */}
            <div className="flex items-center justify-center gap-2 py-1 text-slate-500">
              <div className="h-px bg-slate-800 flex-1"></div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-teal-400">
                <span>Temporal & Statistical Correlation Engine</span>
                <ArrowDown className="w-3.5 h-3.5" />
              </div>
              <div className="h-px bg-slate-800 flex-1"></div>
            </div>

            {/* Pipeline Stage 2: Evidence Correlation Summary */}
            <div className="bg-slate-950/90 border border-teal-500/20 rounded p-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <span className="text-xs font-mono font-semibold text-teal-300 uppercase tracking-wider">
                  Correlated Multi-Signal Matrix
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Calculated against baseline {incidentDetail.service}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                Correlated {incidentDetail.evidenceTimeline.length} discrete telemetry anomalies across deployment timestamp, error rate surges, and alerting rules. Isolation Forest scored deviation at{' '}
                <span className="font-mono text-amber-400">
                  {incidentDetail.mlAnalysis.anomaly.score}
                </span>{' '}
                with strongest weight pointing to recent deployment change.
              </p>
            </div>

            {/* Downward Transition to Causes */}
            <div className="flex items-center justify-center gap-2 py-1 text-slate-500">
              <div className="h-px bg-slate-800 flex-1"></div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-teal-400">
                <span>Ranked Causal Candidates</span>
                <ArrowDown className="w-3.5 h-3.5" />
              </div>
              <div className="h-px bg-slate-800 flex-1"></div>
            </div>

            {/* Pipeline Stage 3: Top Cause Highlight */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {incidentDetail.rootCauseCandidates.slice(0, 2).map((rc, idx) => (
                <div
                  key={rc.id}
                  className="bg-slate-950/80 border border-slate-800 rounded p-3.5 flex items-start justify-between"
                >
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono text-slate-400 uppercase">
                      Rank #{idx + 1} Hypothesis
                    </span>
                    <h4 className="text-xs font-mono font-bold text-slate-100">
                      {rc.candidate}
                    </h4>
                    <p className="text-[11px] text-slate-400 line-clamp-2">{rc.explanation}</p>
                  </div>
                  <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-teal-500/10 text-teal-400 border border-teal-500/30 shrink-0 ml-3">
                    {Math.round(rc.score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Side by side: Timeline and Root Cause Candidates */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EvidenceTimeline
              events={incidentDetail.evidenceTimeline}
              title="Correlated Incident Events"
              subtitle="Temporal sequence of events that contributed to the incident."
            />
            <RootCauseList candidates={incidentDetail.rootCauseCandidates} />
          </div>
        </>
      )}
    </div>
  );
};
