import React, { useEffect, useState } from 'react';
import {
  Printer,
  CheckCircle2,
} from 'lucide-react';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { getIncidents } from '@/api/incidents';
import { getIncidentReport } from '@/api/reports';
import { Incident, IncidentDetails } from '@/types';

export const ReportsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string>('INC-8492');
  const [incident, setIncident] = useState<IncidentDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadIncidents() {
      const res = await getIncidents();
      setIncidents(res.data);
      if (res.data.length > 0 && !res.data.some((i) => i.id === selectedId)) {
        setSelectedId(res.data[0].id);
      }
    }
    loadIncidents();
  }, []);

  useEffect(() => {
    async function loadReport() {
      if (!selectedId) return;
      setLoading(true);
      const res = await getIncidentReport(selectedId);
      setIncident(res.data.incident);
      setLoading(false);
    }
    loadReport();
  }, [selectedId]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Banner & Navigation Controls (Hidden in print) */}
      <div className="no-print space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
              Incident Post-Mortem Report
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-teal-300 font-semibold focus:outline-none focus:border-teal-500"
            >
              {incidents.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.id} — {inc.service}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-2 rounded bg-teal-500 hover:bg-teal-600 text-slate-950 font-bold font-mono text-xs transition-colors shadow-sm cursor-pointer"
            >
              <Printer className="w-4 h-4" />
              <span>Print Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* FORMAL REPORT DOCUMENT CONTAINER (Formatted for print) */}
      {loading ? (
        <div className="py-20 text-center font-mono text-sm text-slate-400">
          Compiling investigation report dossier...
        </div>
      ) : incident ? (
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-6 sm:p-10 space-y-8 print:p-0 print:border-none print:bg-white print:text-black">
          {/* Report Dossier Header */}
          <div className="border-b border-slate-800 pb-6 print:border-slate-300">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-mono tracking-widest uppercase text-teal-400 print:text-slate-700 block">
                  IntelliIncident &bull; Incident Post-Mortem Dossier
                </span>
                <h2 className="text-2xl font-bold font-mono text-slate-100 print:text-black mt-1">
                  {incident.id}: {incident.title}
                </h2>
                <span className="text-xs text-slate-400 print:text-slate-600 block mt-1">
                  Service Domain: <strong className="text-slate-200 print:text-black">{incident.service}</strong> &bull; Incident Timestamp: {incident.timestamp}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={incident.severity} />
                <RiskBadge risk={incident.risk} score={incident.riskScore} showScore />
                <StatusBadge status={incident.status} />
              </div>
            </div>
          </div>

          {/* Section 1: Incident Overview */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-teal-400 print:text-slate-800 border-b border-slate-800 pb-1.5 print:border-slate-300">
              1. Incident Overview
            </h3>
            <p className="text-xs sm:text-sm text-slate-300 print:text-slate-800 leading-relaxed font-sans">
              {incident.summary}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs font-mono">
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300">
                <span className="text-slate-400 print:text-slate-600 text-[10px] block uppercase">Affected Users</span>
                <span className="text-sm font-bold text-rose-400 print:text-rose-600">
                  {incident.metrics.affectedUsers.toLocaleString()}
                </span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300">
                <span className="text-slate-400 print:text-slate-600 text-[10px] block uppercase">Peak Error Rate</span>
                <span className="text-sm font-bold text-rose-400 print:text-rose-600">
                  {incident.metrics.errorRate}%
                </span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300">
                <span className="text-slate-400 print:text-slate-600 text-[10px] block uppercase">P99 Latency Surge</span>
                <span className="text-sm font-bold text-amber-400 print:text-amber-600">
                  {incident.metrics.latencyP99}ms
                </span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300">
                <span className="text-slate-400 print:text-slate-600 text-[10px] block uppercase">Deployment Proximity</span>
                <span className="text-sm font-bold text-cyan-400 print:text-cyan-600">
                  {incident.metrics.deploymentRecencyMinutes}m prior
                </span>
              </div>
            </div>
          </div>

          {/* Section 2: ML Analysis */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-teal-400 print:text-slate-800 border-b border-slate-800 pb-1.5 print:border-slate-300">
              2. Machine Learning Inference Telemetry
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-400 print:text-slate-600">Model:</span>
                  <span className="font-semibold text-slate-200 print:text-black">
                    {incident.mlAnalysis.anomaly.model}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 print:text-slate-600">Anomaly Status:</span>
                  <span className="text-rose-400 font-bold">
                    {incident.mlAnalysis.anomaly.detected ? 'DETECTED' : 'NORMAL'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 print:text-slate-600">Anomaly Outlier Score:</span>
                  <span className="text-slate-200 print:text-black">
                    {incident.mlAnalysis.anomaly.score} / 1.00
                  </span>
                </div>
              </div>

              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-400 print:text-slate-600">Severity Model:</span>
                  <span className="font-semibold text-slate-200 print:text-black">
                    {incident.mlAnalysis.severityPrediction.model}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 print:text-slate-600">Predicted Class:</span>
                  <span className="font-bold text-rose-400">
                    {incident.mlAnalysis.severityPrediction.predictedSeverity}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 print:text-slate-600">Confidence Score:</span>
                  <span className="text-slate-200 print:text-black">
                    {(incident.mlAnalysis.severityPrediction.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Fuzzy Risk Assessment */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-teal-400 print:text-slate-800 border-b border-slate-800 pb-1.5 print:border-slate-300">
              3. Soft Computing Fuzzy Risk Assessment
            </h3>
            <div className="p-4 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300 text-xs font-mono space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span>
                  Evaluated Composite Risk Score:{' '}
                  <strong className="text-rose-400 text-sm">{incident.fuzzyRisk.riskScore}/100</strong>{' '}
                  ({incident.fuzzyRisk.riskLevel})
                </span>
                <span className="text-slate-400 print:text-slate-600">
                  Defuzzification: {incident.fuzzyRisk.defuzzificationMethod}
                </span>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-slate-800/80 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Dominant Triggered Heuristic Rules:
                </span>
                {incident.fuzzyRisk.triggeredRules.map((rule) => (
                  <div key={rule.id} className="text-[11px] text-slate-300 print:text-slate-800">
                    <span className="text-amber-400 print:text-amber-700 font-bold">{rule.id}:</span>{' '}
                    {rule.ruleText}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 4: Evidence Timeline */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-teal-400 print:text-slate-800 border-b border-slate-800 pb-1.5 print:border-slate-300">
              4. Evidence Timeline Sequence
            </h3>
            <div className="space-y-2 font-mono text-xs">
              {incident.evidenceTimeline.map((ev) => (
                <div
                  key={ev.id}
                  className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-teal-400 print:text-teal-700 font-bold text-[11px]">
                      {ev.timestamp.substring(11, 19)} UTC
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 print:bg-slate-200 text-[10px] text-slate-300 print:text-slate-700 border border-slate-800 print:border-slate-400">
                      {ev.eventType}
                    </span>
                  </div>
                  <span className="text-slate-200 print:text-slate-800 flex-1 sm:ml-4 font-sans text-xs">
                    {ev.description}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 5: Root Cause Candidates */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-teal-400 print:text-slate-800 border-b border-slate-800 pb-1.5 print:border-slate-300">
              5. Ranked Root Cause Hypotheses
            </h3>
            <div className="space-y-3 font-mono text-xs">
              {incident.rootCauseCandidates.map((rc, idx) => (
                <div
                  key={rc.id}
                  className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200 print:text-black">
                      #{idx + 1} {rc.candidate}
                    </span>
                    <span className="text-teal-400 font-bold">
                      Confidence: {(rc.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 print:text-slate-700 font-sans">
                    {rc.explanation}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Section 6: Recommendations */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-teal-400 print:text-slate-800 border-b border-slate-800 pb-1.5 print:border-slate-300">
              6. Recommended Remediation & Action Items
            </h3>
            <div className="space-y-2 font-mono text-xs">
              {incident.recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className="p-3 bg-slate-950/80 rounded border border-slate-800 print:bg-slate-100 print:border-slate-300 flex items-start gap-2"
                >
                  <CheckCircle2 className="w-4 h-4 text-teal-400 print:text-teal-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-slate-200 print:text-black">{rec.title}</span>
                    <p className="text-[11px] text-slate-400 print:text-slate-600 font-sans mt-0.5">
                      {rec.description}
                    </p>
                    {rec.actionCmd && (
                      <code className="mt-1 block text-[10px] text-teal-300 print:text-teal-800 font-mono bg-black/60 print:bg-slate-200 px-2 py-0.5 rounded">
                        {rec.actionCmd}
                      </code>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Dossier Sign-off Footer */}
          <div className="pt-6 border-t border-slate-800 print:border-slate-300 text-[11px] font-mono text-slate-500 print:text-slate-600 flex flex-col sm:flex-row justify-between gap-2">
            <span>Generated by IntelliIncident Operations Platform</span>
            <span>SRE Post-Mortem &bull; Evidence-Based Investigation Dossier</span>
          </div>
        </div>
      ) : null}
    </div>
  );
};
