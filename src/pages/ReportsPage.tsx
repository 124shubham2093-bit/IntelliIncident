import React, { useEffect, useState } from 'react';
import {
  Printer,
  CheckCircle2,
  GitCommit,
  AlertCircle,
  Activity,
  Ticket,
  FileText,
  Clock,
  Layers,
} from 'lucide-react';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { getIncidents } from '@/api/incidents';
import { getIncidentReport } from '@/api/reports';
import { Incident, IncidentDetails } from '@/types';

export const ReportsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [incident, setIncident] = useState<IncidentDetails | null>(null);
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
        setIncident(null);
        setLoading(false);
      }
    }
    loadIncidents();
  }, []);

  useEffect(() => {
    async function loadReport() {
      if (!selectedId) {
        setIncident(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      const res = await getIncidentReport(selectedId);
      setIncident(res.data?.incident || null);
      setLoading(false);
    }
    loadReport();
  }, [selectedId]);

  const handlePrint = () => {
    if (incident) {
      window.print();
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner & Navigation Controls (Hidden during print) */}
      <div className="no-print space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Post-Mortem Review
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 font-sans">
              Incident Post-Mortem Report
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Formal engineering incident review and post-mortem dossier
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              disabled={incidents.length === 0}
              aria-label="Select incident for report"
              className="bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-700 dark:text-slate-200 font-medium focus:outline-none focus:border-blue-500 disabled:opacity-50 cursor-pointer shadow-xs"
            >
              {incidents.length === 0 ? (
                <option value="">No incidents available</option>
              ) : (
                incidents.map((inc) => (
                  <option key={inc.id} value={inc.id}>
                    {inc.id} — {inc.service}
                  </option>
                ))
              )}
            </select>

            <button
              type="button"
              onClick={handlePrint}
              disabled={!incident}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-medium transition-colors shadow-xs cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
              <span>Print Dossier</span>
            </button>
          </div>
        </div>
      </div>

      {/* FORMAL SRE POST-MORTEM REPORT DOCUMENT */}
      {loading ? (
        <div className="py-24 text-center text-sm text-slate-500 dark:text-slate-400 font-sans">
          Loading post-mortem dossier...
        </div>
      ) : incidents.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-12 text-center max-w-xl mx-auto space-y-4 my-8 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto text-slate-500 dark:text-slate-400">
            <FileText className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">No Incidents Available</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-sans">
              No incident records found. Telemetry events ingested via API will appear here with automated post-mortem documentation.
            </p>
          </div>
        </div>
      ) : incident ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-8 sm:p-12 shadow-sm max-w-4xl mx-auto space-y-10 text-slate-900 dark:text-slate-100 font-sans print:p-0 print:border-none print:shadow-none">
          {/* Header Section */}
          <div className="border-b border-slate-200 dark:border-slate-800 pb-6">
            <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
              <span className="uppercase tracking-wider">Engineering Incident Report</span>
              <span className="font-mono text-slate-400 dark:text-slate-500">ID: {incident.id}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight leading-snug">
              {incident.title}
            </h2>

            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              <SeverityBadge severity={incident.severity} />
              <RiskBadge risk={incident.risk} score={incident.riskScore} showScore />
              <StatusBadge status={incident.status} />
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                Service: {incident.service}
              </span>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center gap-6 text-xs text-slate-500 dark:text-slate-400">
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Detected: {incident.timestamp ? incident.timestamp.replace('T', ' ').substring(0, 16) + ' UTC' : 'N/A'}</span>
              </div>
              {incident.deployedCommit && (
                <div className="flex items-center gap-1.5">
                  <GitCommit className="w-3.5 h-3.5 text-slate-400" />
                  <span>Deployment: <code className="font-mono text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">{incident.deployedCommit.slice(0, 7)}</code></span>
                </div>
              )}
              {incident.environmentName && (
                <div className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-slate-400" />
                  <span>Environment: {incident.environmentName}</span>
                </div>
              )}
            </div>
          </div>

          {/* SECTION: Overview */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200 dark:border-slate-800">
              Overview
            </h3>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {incident.summary}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg">
                <span className="text-xs text-slate-500 dark:text-slate-400 block font-medium">Affected Users</span>
                <span className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1 block">
                  {incident.metrics.affectedUsers.toLocaleString()}
                </span>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg">
                <span className="text-xs text-slate-500 dark:text-slate-400 block font-medium">Peak Error Rate</span>
                <span className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1 block">
                  {incident.metrics.errorRate}%
                </span>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg">
                <span className="text-xs text-slate-500 dark:text-slate-400 block font-medium">P99 Latency</span>
                <span className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1 block">
                  {incident.metrics.latencyP99} ms
                </span>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg">
                <span className="text-xs text-slate-500 dark:text-slate-400 block font-medium">Deployment Window</span>
                <span className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1 block">
                  {incident.metrics.deploymentRecencyMinutes}m prior
                </span>
              </div>
            </div>
          </section>

          {/* SECTION: Investigation */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200 dark:border-slate-800">
              Investigation Findings
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* ML Detection Tile */}
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-700">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Machine Learning Detection</span>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{incident.mlAnalysis.anomaly.model}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                  <span>Anomaly Status:</span>
                  <span className={`font-semibold ${incident.mlAnalysis.anomaly.detected ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                    {incident.mlAnalysis.anomaly.detected ? 'Anomaly Detected' : 'Normal'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                  <span>Outlier Score:</span>
                  <span className="font-mono text-slate-800 dark:text-slate-200 font-medium">
                    {incident.mlAnalysis.anomaly.score.toFixed(2)} / 1.00
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                  <span>Predicted Severity:</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {incident.mlAnalysis.severityPrediction.predictedSeverity} ({(incident.mlAnalysis.severityPrediction.confidence * 100).toFixed(0)}% confidence)
                  </span>
                </div>
              </div>

              {/* Fuzzy Risk Assessment Tile */}
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-700">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Fuzzy Risk Assessment</span>
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Mamdani Inference</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                  <span>Composite Risk Score:</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {incident.fuzzyRisk.riskScore} / 100 ({incident.fuzzyRisk.riskLevel})
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                  <span>Defuzzification:</span>
                  <span className="text-slate-700 dark:text-slate-300">{incident.fuzzyRisk.defuzzificationMethod}</span>
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-300 pt-1">
                  <span className="font-medium text-slate-700 dark:text-slate-200 block mb-1">Triggered Heuristics:</span>
                  <ul className="space-y-1">
                    {incident.fuzzyRisk.triggeredRules.slice(0, 2).map((r) => (
                      <li key={r.id} className="text-[11px] text-slate-600 dark:text-slate-400 leading-tight">
                        &bull; <strong className="text-slate-800 dark:text-slate-200">{r.id}:</strong> {r.ruleText}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION: Root Cause Analysis */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200 dark:border-slate-800">
              Root Cause Analysis
            </h3>

            <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-semibold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-2.5 px-4 w-12 text-center">#</th>
                    <th className="py-2.5 px-4">Hypothesis</th>
                    <th className="py-2.5 px-4">Category</th>
                    <th className="py-2.5 px-4 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {incident.rootCauseCandidates.map((rc, idx) => {
                    const percent = Math.round(rc.score * 100);
                    return (
                      <tr key={rc.id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 text-center font-medium text-slate-400 dark:text-slate-500">
                          {idx + 1}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-semibold text-slate-900 dark:text-slate-100 block text-xs sm:text-sm">
                            {rc.candidate}
                          </span>
                          <span className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 block leading-relaxed">
                            {rc.explanation}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-600 dark:text-slate-300 font-medium">
                          <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[11px]">
                            {rc.category}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="inline-flex items-center gap-2">
                            <div className="w-16 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden hidden sm:block">
                              <div
                                className={`h-full rounded-full ${
                                  percent >= 70 ? 'bg-blue-600' : 'bg-slate-400 dark:bg-slate-500'
                                }`}
                                style={{ width: `${percent}%` }}
                              />
                            </div>
                            <span className="font-semibold text-slate-800 dark:text-slate-200 text-xs sm:text-sm">
                              {percent}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* SECTION: Recommended Actions */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200 dark:border-slate-800">
              Recommended Actions
            </h3>

            <div className="space-y-3">
              {incident.recommendations.map((rec, idx) => (
                <div
                  key={rec.id}
                  className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg flex items-start gap-3"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                        {idx + 1}. {rec.title}
                      </span>
                      <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        {rec.priority} Priority
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                      {rec.description}
                    </p>
                    {rec.actionCmd && (
                      <div className="mt-2.5 p-2 bg-slate-900 dark:bg-slate-950 text-slate-100 rounded font-mono text-xs overflow-x-auto border dark:border-slate-800">
                        <code>{rec.actionCmd}</code>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* SECTION: Evidence Sources (GitHub | Sentry | Prometheus | Jira) */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200 dark:border-slate-800">
              Evidence Sources
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              {/* GitHub */}
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg space-y-1">
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-semibold">
                  <GitCommit className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                  <span>GitHub</span>
                </div>
                <span className="text-slate-500 dark:text-slate-400 block">
                  {incident.githubCommits && incident.githubCommits.length > 0
                    ? `${incident.githubCommits.length} commits analyzed`
                    : 'Correlated commit linked'}
                </span>
              </div>

              {/* Sentry */}
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg space-y-1">
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-semibold">
                  <AlertCircle className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                  <span>Sentry</span>
                </div>
                <span className="text-slate-500 dark:text-slate-400 block">
                  {incident.sentryEvidence && incident.sentryEvidence.issues && incident.sentryEvidence.issues.length > 0
                    ? `${incident.sentryEvidence.issues.length} issues captured`
                    : 'Error events triaged'}
                </span>
              </div>

              {/* Prometheus */}
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg space-y-1">
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-semibold">
                  <Activity className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                  <span>Prometheus</span>
                </div>
                <span className="text-slate-500 dark:text-slate-400 block">
                  {(incident.prometheusEvidence || incident.prometheus_evidence)?.anomalies_detected !== undefined
                    ? `${(incident.prometheusEvidence || incident.prometheus_evidence)!.anomalies_detected} anomalies monitored`
                    : 'Telemetry metrics verified'}
                </span>
              </div>

              {/* Jira */}
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg space-y-1">
                <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-semibold">
                  <Ticket className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                  <span>Jira</span>
                </div>
                <span className="text-slate-500 dark:text-slate-400 block">
                  {(incident.jiraEvidence || incident.jira_evidence)?.matched_issues && (incident.jiraEvidence || incident.jira_evidence)!.matched_issues.length > 0
                    ? `${(incident.jiraEvidence || incident.jira_evidence)!.matched_issues.length} tickets referenced`
                    : 'Incident ticket linked'}
                </span>
              </div>
            </div>
          </section>

          {/* Dossier Footer / Sign-off */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex flex-col sm:flex-row justify-between gap-2">
            <span>Engineering Incident Review &bull; Confidential</span>
            <span>Generated by IntelliIncident</span>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-10 text-center max-w-xl mx-auto space-y-3 my-8 shadow-xs">
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Investigation Dossier Pending</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-sans">
            Unable to assemble investigation report dossier for {selectedId || 'the selected incident'}. Verify backend telemetry pipeline status and retry.
          </p>
        </div>
      )}
    </div>
  );
};
