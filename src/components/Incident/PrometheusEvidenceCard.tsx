import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  HardDrive,
  BarChart3,
  Flame,
  Clock,
  Radio,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { PrometheusEvidence, RootCauseCandidate, PrometheusMetricSample } from '@/types';

interface PrometheusEvidenceCardProps {
  evidence: PrometheusEvidence;
  rootCauseCandidates?: RootCauseCandidate[];
}

export const PrometheusEvidenceCard: React.FC<PrometheusEvidenceCardProps> = ({
  evidence,
  rootCauseCandidates = [],
}) => {
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);

  const getMetricIcon = (metricKey: string) => {
    switch (metricKey) {
      case 'cpu_utilization':
        return <Cpu className="w-3.5 h-3.5 text-cyan-400" />;
      case 'memory_utilization':
        return <HardDrive className="w-3.5 h-3.5 text-indigo-400" />;
      case 'request_rate':
        return <BarChart3 className="w-3.5 h-3.5 text-blue-400" />;
      case 'error_rate':
        return <Flame className="w-3.5 h-3.5 text-rose-400" />;
      case 'p95_latency':
        return <Clock className="w-3.5 h-3.5 text-amber-400" />;
      case 'availability':
        return <Radio className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-teal-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CONNECTED':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Connected & Correlated</span>
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            Unconfigured
          </span>
        );
      case 'UNAVAILABLE':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            <span>Prometheus Offline</span>
          </span>
        );
      case 'NO_METRICS_FOUND':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>No Metrics In Range</span>
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  const isMetricCitedInRCA = (metricKey: string): boolean => {
    if (!rootCauseCandidates || rootCauseCandidates.length === 0) return false;
    const nameMap: Record<string, string[]> = {
      cpu_utilization: ['cpu', 'processor'],
      memory_utilization: ['memory', 'ram', 'leak'],
      request_rate: ['request rate', 'traffic', 'load spike'],
      error_rate: ['error rate', 'http 5xx', 'failure rate'],
      p95_latency: ['latency', 'p95', 'slow'],
      availability: ['availability', 'uptime', 'down'],
    };
    const keywords = nameMap[metricKey] || [metricKey];
    return rootCauseCandidates.some((candidate) =>
      candidate.evidence.some((ev) =>
        keywords.some((kw) => ev.toLowerCase().includes(kw))
      )
    );
  };

  // Compile list of metric samples
  const metricItems: { key: string; sample: PrometheusMetricSample }[] = [];
  if (evidence.cpu_utilization) metricItems.push({ key: 'cpu_utilization', sample: evidence.cpu_utilization });
  if (evidence.memory_utilization) metricItems.push({ key: 'memory_utilization', sample: evidence.memory_utilization });
  if (evidence.request_rate) metricItems.push({ key: 'request_rate', sample: evidence.request_rate });
  if (evidence.error_rate) metricItems.push({ key: 'error_rate', sample: evidence.error_rate });
  if (evidence.p95_latency) metricItems.push({ key: 'p95_latency', sample: evidence.p95_latency });
  if (evidence.availability) metricItems.push({ key: 'availability', sample: evidence.availability });

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
            Prometheus Metric Telemetry Intelligence
          </h3>
          {evidence.service && (
            <span className="text-xs font-mono text-slate-400 hidden md:inline">
              (Service: {evidence.service})
            </span>
          )}
        </div>
        <div>{getStatusBadge(evidence.status)}</div>
      </div>

      {/* Overview Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs font-mono">
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Anomalies Detected</span>
          <span
            className={`font-bold text-sm block mt-0.5 ${
              evidence.anomalies_detected > 0 ? 'text-rose-400' : 'text-emerald-400'
            }`}
          >
            {evidence.anomalies_detected}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Peak Correlation</span>
          <span
            className={`font-semibold block mt-0.5 truncate ${
              evidence.highest_correlation === 'HIGH'
                ? 'text-rose-400 font-bold'
                : evidence.highest_correlation === 'MEDIUM'
                ? 'text-amber-400'
                : evidence.highest_correlation === 'LOW'
                ? 'text-blue-400'
                : 'text-slate-400'
            }`}
          >
            {evidence.highest_correlation || 'NONE'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Prometheus Host</span>
          <span className="text-cyan-400 font-semibold block mt-0.5 truncate" title={evidence.url}>
            {evidence.url || 'None'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Time Window</span>
          <span className="text-slate-300 font-semibold block mt-0.5 truncate">
            {evidence.time_window ? 'T-60m Baseline vs Incident' : 'Default / Live'}
          </span>
        </div>
      </div>

      {/* Summary / Message */}
      <p className="text-xs text-slate-300 font-sans italic bg-slate-950/50 p-2.5 rounded border border-slate-800/60">
        {evidence.summary}
      </p>

      {/* Time Window Details Banner (if present) */}
      {evidence.time_window && (
        <div className="bg-slate-950/40 p-2 rounded border border-slate-800/40 text-[11px] font-mono text-slate-400 flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="text-slate-500">Baseline Window: </span>
            <span className="text-slate-300">
              {new Date(evidence.time_window.baseline_start).toLocaleTimeString()} -{' '}
              {new Date(evidence.time_window.baseline_end).toLocaleTimeString()}
            </span>
          </div>
          <div>
            <span className="text-slate-500">Incident Window: </span>
            <span className="text-amber-300">
              {new Date(evidence.time_window.incident_start).toLocaleTimeString()} -{' '}
              {new Date(evidence.time_window.incident_end).toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}

      {/* Metric Telemetry Samples */}
      {metricItems.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 font-semibold">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span>Evaluated Metric Deviations ({metricItems.length})</span>
          </div>

          <div className="bg-slate-950 rounded border border-slate-800 overflow-hidden divide-y divide-slate-800/60 font-mono text-xs">
            {metricItems.map(({ key, sample }) => {
              const cited = isMetricCitedInRCA(key);
              const isExpanded = expandedMetric === key;
              const hasAnomaly = sample.anomaly_detected;

              return (
                <div
                  key={key}
                  className={`p-3 space-y-2 hover:bg-slate-900/30 transition-colors ${
                    cited
                      ? 'bg-amber-950/10 border-l-2 border-amber-500'
                      : hasAnomaly
                      ? 'border-l-2 border-rose-500'
                      : ''
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <div className="mt-0.5 shrink-0">{getMetricIcon(key)}</div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-slate-200">{sample.metric_name}</span>
                          {hasAnomaly ? (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                              Anomaly
                            </span>
                          ) : (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              Normal
                            </span>
                          )}
                          {cited && (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                              RCA Cited
                            </span>
                          )}
                          {sample.correlation_strength !== 'NONE' && (
                            <span
                              className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                                sample.correlation_strength === 'HIGH'
                                  ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                  : sample.correlation_strength === 'MEDIUM'
                                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                  : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                              }`}
                            >
                              {sample.correlation_strength} correlation
                            </span>
                          )}
                        </div>

                        {sample.message && (
                          <span className="text-[11px] text-slate-400 block mt-0.5">
                            {sample.message}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Numeric Comparison */}
                    <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto text-right">
                      <div>
                        <span className="text-[10px] text-slate-500 block uppercase">Baseline</span>
                        <span className="text-slate-300 font-semibold">
                          {sample.baseline_value !== null && sample.baseline_value !== undefined
                            ? `${sample.baseline_value.toFixed(1)}${sample.unit}`
                            : 'N/A'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500 block uppercase">Observed</span>
                        <span
                          className={`font-semibold ${
                            hasAnomaly ? 'text-rose-400' : 'text-slate-200'
                          }`}
                        >
                          {sample.observed_value !== null && sample.observed_value !== undefined
                            ? `${sample.observed_value.toFixed(1)}${sample.unit}`
                            : 'N/A'}
                        </span>
                      </div>

                      {sample.deviation_pct !== null && sample.deviation_pct !== undefined && (
                        <div className="min-w-[65px]">
                          <span className="text-[10px] text-slate-500 block uppercase">Deviation</span>
                          <span
                            className={`font-bold flex items-center justify-end gap-0.5 ${
                              Math.abs(sample.deviation_pct) >= 20
                                ? 'text-rose-400'
                                : 'text-emerald-400'
                            }`}
                          >
                            {sample.deviation_pct > 0 ? '+' : ''}
                            {sample.deviation_pct.toFixed(1)}%
                          </span>
                        </div>
                      )}

                      <button
                        onClick={() => setExpandedMetric(isExpanded ? null : key)}
                        className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                        title={isExpanded ? 'Collapse PromQL' : 'View PromQL'}
                      >
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* PromQL Query Expansion */}
                  {isExpanded && (
                    <div className="bg-slate-900/80 p-2.5 rounded border border-slate-800 text-[11px] space-y-1 mt-1">
                      <div className="flex items-center justify-between text-[10px] text-slate-500 uppercase">
                        <span>Executed PromQL Expression</span>
                        <span>Unit: {sample.unit}</span>
                      </div>
                      <pre className="text-cyan-300 bg-slate-950 p-2 rounded border border-slate-800/80 overflow-x-auto whitespace-pre font-mono">
                        {sample.query}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
