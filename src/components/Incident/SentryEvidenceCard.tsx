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
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Connected & Correlated</span>
          </span>
        );
      case 'NO_ISSUES_FOUND':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            <span>0 Active Issues</span>
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            Unconfigured
          </span>
        );
      case 'RATE_LIMITED':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Rate Limited</span>
          </span>
        );
      case 'AUTH_ERROR':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            <span>Authentication Failed</span>
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

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-red-600" />
          <h3 className="text-sm font-semibold text-slate-900">
            Sentry Runtime Error Intelligence
          </h3>
          {evidence.org_slug && evidence.project_slug && (
            <span className="text-xs text-slate-500 hidden md:inline">
              ({evidence.org_slug}/{evidence.project_slug})
            </span>
          )}
        </div>
        <div>{getStatusBadge(evidence.status)}</div>
      </div>

      {/* Overview Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Active Issues</span>
          <span className="text-red-600 font-bold text-base block mt-0.5">
            {evidence.issue_count}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Matched Exception</span>
          <span
            className="text-amber-800 font-semibold block mt-0.5 truncate"
            title={evidence.matched_exception_type || 'None'}
          >
            {evidence.matched_exception_type || 'None detected'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Correlated Release</span>
          <span
            className="text-blue-700 font-semibold block mt-0.5 truncate font-mono text-[11px]"
            title={evidence.correlated_release || 'None'}
          >
            {evidence.correlated_release
              ? evidence.correlated_release.slice(0, 10)
              : 'None'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Environment</span>
          <span className="text-emerald-700 font-semibold block mt-0.5 truncate">
            {evidence.correlated_environment || 'All environments'}
          </span>
        </div>
      </div>

      {/* Diagnostic Message */}
      <p className="text-xs text-slate-700 bg-white p-3 rounded-md border border-slate-200 leading-relaxed">
        {evidence.message}
      </p>

      {/* Matched Stack Trace Frames */}
      {evidence.matched_stack_trace_frames && evidence.matched_stack_trace_frames.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-800 font-semibold">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            <span>Sentry Diagnostic Stack Frames ({evidence.matched_stack_trace_frames.length})</span>
          </div>
          <div className="bg-white rounded-md border border-slate-200 overflow-hidden divide-y divide-slate-100 text-xs">
            {evidence.matched_stack_trace_frames.map((frame, idx) => {
              const cited = isFrameCitedInRCA(frame.filename);
              return (
                <div
                  key={idx}
                  className={`p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors ${
                    cited ? 'bg-red-50/50 border-l-2 border-red-500' : ''
                  }`}
                >
                  <div className="flex items-start gap-2 min-w-0">
                    <FileCode className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${cited ? 'text-red-600' : 'text-slate-400'}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono font-semibold truncate ${cited ? 'text-red-700' : 'text-slate-800'}`}>
                          {frame.filename || 'unknown'}
                        </span>
                        {frame.lineno && (
                          <span className="text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 font-mono">
                            line {frame.lineno}
                          </span>
                        )}
                        {cited && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-800 border border-red-200 font-medium">
                            Cross-Source Matched
                          </span>
                        )}
                      </div>
                      {frame.function && (
                        <span className="text-[11px] text-slate-500 font-mono block truncate mt-0.5">
                          fn: {frame.function}
                        </span>
                      )}
                      {frame.context_line && (
                        <pre className="text-[11px] font-mono text-slate-800 bg-slate-100 p-1.5 rounded mt-1 overflow-x-auto whitespace-pre">
                          {frame.context_line.trim()}
                        </pre>
                      )}
                    </div>
                  </div>
                  {frame.in_app && (
                    <span className="text-[10px] text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200 shrink-0 self-start sm:self-auto font-medium">
                      in_app
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Detailed Issues List */}
      {evidence.issues && evidence.issues.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider block">
            Recent Sentry Issue Events:
          </span>
          <div className="space-y-2">
            {evidence.issues.map((issue) => {
              const isExpanded = expandedIssueId === issue.id;
              return (
                <div
                  key={issue.id}
                  className="bg-white border border-slate-200 rounded-md overflow-hidden text-xs"
                >
                  <div
                    onClick={() => setExpandedIssueId(isExpanded ? null : issue.id)}
                    className="p-3 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-50"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-semibold text-slate-800 truncate">
                        {issue.title}
                      </span>
                      {issue.short_id && (
                        <span className="font-mono text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                          {issue.short_id}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="flex items-center gap-1 text-slate-500 text-[11px]">
                        <Flame className="w-3 h-3 text-red-500" />
                        <span>{issue.count} events</span>
                      </span>
                      <span className="flex items-center gap-1 text-slate-500 text-[11px]">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{issue.last_seen ? new Date(issue.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'recently'}</span>
                      </span>
                      {issue.permalink && (
                        <a
                          href={issue.permalink}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {isExpanded && issue.culprit && (
                    <div className="px-3 pb-3 pt-1 border-t border-slate-100 bg-slate-50 text-[11px] space-y-1">
                      <span className="text-slate-500 font-semibold block">Culprit:</span>
                      <code className="text-slate-800 font-mono block break-all">
                        {issue.culprit}
                      </code>
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
