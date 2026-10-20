import React, { useState } from 'react';
import {
  Bug,
  ExternalLink,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ChevronDown,
  ChevronUp,
  Clock,
  Flame,
} from 'lucide-react';
import { SentryEvidence, RootCauseCandidate } from '@/types';

interface SentryEvidenceCardProps {
  evidence: SentryEvidence;
  rootCauseCandidates?: RootCauseCandidate[];
}

export const SentryEvidenceCard: React.FC<SentryEvidenceCardProps> = ({
  evidence,
  rootCauseCandidates = [],
}) => {
  const [expandedIssueId, setExpandedIssueId] = useState<string | null>(null);

  const isFrameCitedInRCA = (filename?: string | null): boolean => {
    if (!filename || !rootCauseCandidates || rootCauseCandidates.length === 0) return false;
    const baseName = filename.replace(/\\/g, '/').split('/').pop() || filename;
    return rootCauseCandidates.some((candidate) =>
      candidate.evidence.some(
        (ev) =>
          ev.includes(`'${filename}'`) ||
          (baseName.length >= 4 && ev.includes(`'${baseName}'`))
      )
    );
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
      case 'NO_ISSUES_FOUND':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-sky-400" />
            <span>0 Active Issues</span>
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            Unconfigured
          </span>
        );
      case 'RATE_LIMITED':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>Rate Limited</span>
          </span>
        );
      case 'AUTH_ERROR':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            <span>Authentication Failed</span>
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

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-rose-400" />
          <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
            Sentry Runtime Error Intelligence
          </h3>
          {evidence.org_slug && evidence.project_slug && (
            <span className="text-xs font-mono text-slate-400 hidden md:inline">
              ({evidence.org_slug}/{evidence.project_slug})
            </span>
          )}
        </div>
        <div>{getStatusBadge(evidence.status)}</div>
      </div>

      {/* Overview Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs font-mono">
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Active Issues</span>
          <span className="text-rose-400 font-bold text-sm block mt-0.5">
            {evidence.issue_count}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Matched Exception</span>
          <span
            className="text-amber-300 font-semibold block mt-0.5 truncate"
            title={evidence.matched_exception_type || 'None'}
          >
            {evidence.matched_exception_type || 'None detected'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Correlated Release</span>
          <span
            className="text-cyan-400 font-semibold block mt-0.5 truncate"
            title={evidence.correlated_release || 'None'}
          >
            {evidence.correlated_release
              ? evidence.correlated_release.slice(0, 10)
              : 'None'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Environment</span>
          <span className="text-emerald-400 font-semibold block mt-0.5 truncate">
            {evidence.correlated_environment || 'All environments'}
          </span>
        </div>
      </div>

      {/* Diagnostic Message */}
      <p className="text-xs text-slate-300 font-sans italic bg-slate-950/50 p-2.5 rounded border border-slate-800/60">
        {evidence.message}
      </p>

      {/* Matched Stack Trace Frames */}
      {evidence.matched_stack_trace_frames && evidence.matched_stack_trace_frames.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 font-semibold">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Sentry Diagnostic Stack Frames ({evidence.matched_stack_trace_frames.length})</span>
          </div>
          <div className="bg-slate-950 rounded border border-slate-800 overflow-hidden divide-y divide-slate-800/60 font-mono text-xs">
            {evidence.matched_stack_trace_frames.map((frame, idx) => {
              const cited = isFrameCitedInRCA(frame.filename);
              return (
                <div
                  key={idx}
                  className={`p-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-900/50 transition-colors ${
                    cited ? 'bg-rose-950/20 border-l-2 border-rose-500' : ''
                  }`}
                >
                  <div className="flex items-start gap-2 min-w-0">
                    <FileCode className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${cited ? 'text-rose-400' : 'text-slate-400'}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold truncate ${cited ? 'text-rose-300' : 'text-slate-200'}`}>
                          {frame.filename || 'unknown'}
                        </span>
                        {frame.lineno && (
                          <span className="text-[10px] text-slate-400 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                            line {frame.lineno}
                          </span>
                        )}
                        {cited && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                            Cross-Source Matched
                          </span>
                        )}
                      </div>
                      {frame.function && (
                        <span className="text-[11px] text-slate-400 block truncate">
                          fn: {frame.function}
                        </span>
                      )}
                      {frame.context_line && (
                        <pre className="text-[10px] text-slate-300 bg-slate-900/70 p-1 rounded mt-1 overflow-x-auto whitespace-pre">
                          {frame.context_line.trim()}
                        </pre>
                      )}
                    </div>
                  </div>
                  {frame.in_app && (
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40 shrink-0 self-start sm:self-auto">
                      in_app
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Sentry Issues List */}
      {evidence.issues && evidence.issues.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold">
            <span className="flex items-center gap-1.5">
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              Unresolved Sentry Issues ({evidence.issues.length})
            </span>
          </div>
          <div className="bg-slate-950 rounded border border-slate-800 divide-y divide-slate-800/60 font-mono text-xs">
            {evidence.issues.map((issue) => {
              const isExpanded = expandedIssueId === issue.id;
              return (
                <div key={issue.id} className="p-3 space-y-2 hover:bg-slate-900/30 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-start gap-2 min-w-0">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 shrink-0">
                        {issue.short_id || `#${issue.id}`}
                      </span>
                      <div className="min-w-0">
                        <span className="text-slate-100 font-semibold block truncate" title={issue.title}>
                          {issue.title}
                        </span>
                        {issue.culprit && (
                          <span className="text-[11px] text-slate-400 block truncate">
                            {issue.culprit}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                      <span className="text-[11px] text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {issue.count} events
                      </span>
                      {issue.permalink && (
                        <a
                          href={issue.permalink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-teal-400 hover:text-teal-300 transition-colors p-1"
                          title="Open in Sentry"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      <button
                        onClick={() => setExpandedIssueId(isExpanded ? null : issue.id)}
                        className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {isExpanded && issue.metadata && Object.keys(issue.metadata).length > 0 && (
                    <div className="bg-slate-900/80 p-2.5 rounded border border-slate-800 text-[11px] space-y-1">
                      <span className="text-[10px] uppercase text-slate-400 font-semibold block">Issue Metadata</span>
                      {Object.entries(issue.metadata).map(([key, val]) => (
                        <div key={key} className="flex items-start gap-2">
                          <span className="text-slate-500 shrink-0">{key}:</span>
                          <span className="text-slate-300 break-all">{String(val)}</span>
                        </div>
                      ))}
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
