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
        return <Cpu className="w-3.5 h-3.5 text-blue-600" />;
      case 'memory_utilization':
        return <HardDrive className="w-3.5 h-3.5 text-indigo-600" />;
      case 'request_rate':
        return <BarChart3 className="w-3.5 h-3.5 text-blue-600" />;
      case 'error_rate':
        return <Flame className="w-3.5 h-3.5 text-red-600" />;
      case 'p95_latency':
        return <Clock className="w-3.5 h-3.5 text-amber-600" />;
      case 'availability':
        return <Radio className="w-3.5 h-3.5 text-emerald-600" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-blue-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CONNECTED':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Connected & Scraped</span>
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            Unconfigured
          </span>
        );
      case 'UNAVAILABLE':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            <span>Prometheus Offline</span>
          </span>
        );
      case 'NO_METRICS_FOUND':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>No Metrics In Range</span>
          </span>
        );
      default:
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
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

  const metricItems: { key: string; sample: PrometheusMetricSample }[] = [];
  if (evidence.cpu_utilization) metricItems.push({ key: 'cpu_utilization', sample: evidence.cpu_utilization });
  if (evidence.memory_utilization) metricItems.push({ key: 'memory_utilization', sample: evidence.memory_utilization });
  if (evidence.request_rate) metricItems.push({ key: 'request_rate', sample: evidence.request_rate });
  if (evidence.error_rate) metricItems.push({ key: 'error_rate', sample: evidence.error_rate });
  if (evidence.p95_latency) metricItems.push({ key: 'p95_latency', sample: evidence.p95_latency });
  if (evidence.availability) metricItems.push({ key: 'availability', sample: evidence.availability });

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-900">
            Prometheus Metric Telemetry
          </h3>
          {evidence.service && (
            <span className="text-xs text-slate-500 hidden md:inline">
              (Service: {evidence.service})
            </span>
          )}
        </div>
        <div>{getStatusBadge(evidence.status)}</div>
      </div>

      {/* Overview Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Anomalies Detected</span>
          <span
            className={`font-bold text-base block mt-0.5 ${
              evidence.anomalies_detected > 0 ? 'text-red-600' : 'text-emerald-700'
            }`}
          >
            {evidence.anomalies_detected}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Peak Correlation</span>
          <span
            className={`font-semibold block mt-0.5 truncate ${
              evidence.highest_correlation === 'HIGH'
                ? 'text-red-600 font-bold'
                : evidence.highest_correlation === 'MEDIUM'
                ? 'text-amber-700'
                : evidence.highest_correlation === 'LOW'
                ? 'text-blue-700'
                : 'text-slate-500'
            }`}
          >
            {evidence.highest_correlation || 'NONE'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Prometheus Host</span>
          <span className="text-slate-800 font-mono text-[11px] font-medium block mt-0.5 truncate" title={evidence.url}>
            {evidence.url || 'None'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Time Window</span>
          <span className="text-slate-800 font-medium block mt-0.5 truncate">
            {evidence.time_window ? 'Baseline vs Incident Window' : 'Default Scrape'}
          </span>
        </div>
      </div>

      {/* Summary Message */}
      <p className="text-xs text-slate-700 bg-white p-3 rounded-md border border-slate-200 leading-relaxed">
        {evidence.summary}
      </p>

      {/* Metric Telemetry Samples */}
      {metricItems.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-800 font-semibold">
            <Activity className="w-3.5 h-3.5 text-blue-600" />
            <span>Evaluated Metric Deviations ({metricItems.length})</span>
          </div>

          <div className="bg-white rounded-md border border-slate-200 overflow-hidden divide-y divide-slate-100 text-xs">
            {metricItems.map(({ key, sample }) => {
              const cited = isMetricCitedInRCA(key);
              const isExpanded = expandedMetric === key;
              const hasAnomaly = sample.anomaly_detected;

              return (
                <div
                  key={key}
                  className={`p-3 space-y-2 hover:bg-slate-50 transition-colors ${
                    cited
                      ? 'bg-amber-50/40 border-l-2 border-amber-500'
                      : hasAnomaly
                      ? 'border-l-2 border-red-500'
                      : ''
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <div className="mt-0.5 shrink-0">{getMetricIcon(key)}</div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-slate-900">{sample.metric_name}</span>
                          {hasAnomaly ? (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-800 border border-red-200 font-medium">
                              Anomaly
                            </span>
                          ) : (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-medium">
                              Normal
                            </span>
                          )}
                          {cited && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200 font-medium">
                              RCA Cited
                            </span>
                          )}
                        </div>

                        {sample.message && (
                          <span className="text-[11px] text-slate-500 block mt-0.5">
                            {sample.message}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Numeric Comparison */}
                    <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto text-right">
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase font-medium">Baseline</span>
                        <span className="text-slate-700 font-semibold font-mono">
                          {sample.baseline_value !== null && sample.baseline_value !== undefined
                            ? `${sample.baseline_value.toFixed(1)}${sample.unit}`
                            : 'N/A'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase font-medium">Observed</span>
                        <span
                          className={`font-semibold font-mono ${
                            hasAnomaly ? 'text-red-600' : 'text-slate-900'
                          }`}
                        >
                          {sample.observed_value !== null && sample.observed_value !== undefined
                            ? `${sample.observed_value.toFixed(1)}${sample.unit}`
                            : 'N/A'}
                        </span>
                      </div>

                      {sample.deviation_pct !== null && sample.deviation_pct !== undefined && (
                        <div className="min-w-[65px]">
                          <span className="text-[10px] text-slate-400 block uppercase font-medium">Deviation</span>
                          <span
                            className={`font-bold font-mono flex items-center justify-end gap-0.5 ${
                              Math.abs(sample.deviation_pct) >= 20
                                ? 'text-red-600'
                                : 'text-emerald-700'
                            }`}
                          >
                            {sample.deviation_pct > 0 ? '+' : ''}
                            {sample.deviation_pct.toFixed(1)}%
                          </span>
                        </div>
                      )}

                      <button
                        onClick={() => setExpandedMetric(isExpanded ? null : key)}
                        className="text-slate-400 hover:text-slate-600 transition-colors p-1"
                        title={isExpanded ? 'Collapse PromQL' : 'View PromQL'}
                      >
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* PromQL Query Expansion */}
                  {isExpanded && (
                    <div className="bg-slate-900 p-2.5 rounded-md text-xs text-slate-200 space-y-1 mt-1 font-mono">
                      <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase">
                        <span>PromQL Query</span>
                        <span>Unit: {sample.unit}</span>
                      </div>
                      <pre className="text-blue-300 overflow-x-auto whitespace-pre">
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
