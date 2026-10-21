import React, { useState } from 'react';
import {
  Ticket,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Tag,
  User,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  BookmarkCheck,
} from 'lucide-react';
import { JiraEvidence, RootCauseCandidate, JiraIssue } from '@/types';

interface JiraEvidenceCardProps {
  evidence: JiraEvidence;
  rootCauseCandidates?: RootCauseCandidate[];
}

export const JiraEvidenceCard: React.FC<JiraEvidenceCardProps> = ({
  evidence,
  rootCauseCandidates = [],
}) => {
  const [expandedIssueKey, setExpandedIssueKey] = useState<string | null>(null);

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
            <span>0 Correlated Issues</span>
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
            <span>Jira Offline</span>
          </span>
        );
      case 'AUTH_ERROR':
        return (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
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

  const isIssueCitedInRCA = (issue: JiraIssue): boolean => {
    if (!rootCauseCandidates || rootCauseCandidates.length === 0) return false;
    return rootCauseCandidates.some((candidate) =>
      candidate.evidence.some(
        (ev) =>
          ev.includes(issue.key) ||
          (issue.summary && ev.toLowerCase().includes(issue.summary.slice(0, 20).toLowerCase()))
      )
    );
  };

  const primary = evidence.primary_issue;
  const isPrimaryCited = primary ? isIssueCitedInRCA(primary) : false;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Ticket className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
            Jira Work Item & Ticket Intelligence
          </h3>
          {evidence.project_key && (
            <span className="text-xs font-mono text-slate-400 hidden md:inline">
              (Project: {evidence.project_key})
            </span>
          )}
        </div>
        <div>{getStatusBadge(evidence.status)}</div>
      </div>

      {/* Overview Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs font-mono">
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Matched Ticket</span>
          <span className="text-sky-400 font-bold text-sm block mt-0.5 truncate">
            {primary ? primary.key : 'None'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Match Confidence</span>
          <span
            className={`font-semibold block mt-0.5 truncate ${
              evidence.correlation_strength === 'HIGH'
                ? 'text-emerald-400 font-bold'
                : evidence.correlation_strength === 'MEDIUM'
                ? 'text-amber-400'
                : evidence.correlation_strength === 'LOW'
                ? 'text-blue-400'
                : 'text-slate-400'
            }`}
          >
            {evidence.correlation
              ? `${Math.round(evidence.correlation.confidence_score * 100)}% (${evidence.correlation_strength})`
              : 'N/A'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Jira Server</span>
          <span className="text-cyan-400 font-semibold block mt-0.5 truncate" title={evidence.base_url}>
            {evidence.base_url ? evidence.base_url.replace(/^https?:\/\//, '') : 'None'}
          </span>
        </div>
        <div className="bg-slate-950/80 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 block uppercase">Matched Candidates</span>
          <span className="text-slate-200 font-semibold block mt-0.5">
            {evidence.matched_issues.length} candidate(s)
          </span>
        </div>
      </div>

      {/* Diagnostic Message */}
      <p className="text-xs text-slate-300 font-sans italic bg-slate-950/50 p-2.5 rounded border border-slate-800/60">
        {evidence.summary}
      </p>

      {/* Primary Correlated Ticket Details */}
      {primary && (
        <div
          className={`bg-slate-950 rounded border border-slate-800 p-4 space-y-3 ${
            isPrimaryCited ? 'border-l-4 border-l-sky-500' : ''
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-start gap-2.5 min-w-0">
              <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30 shrink-0">
                {primary.key}
              </span>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-xs font-semibold text-slate-100">{primary.summary}</h4>
                  {isPrimaryCited && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 border border-sky-500/40 flex items-center gap-1">
                      <BookmarkCheck className="w-3 h-3 text-sky-400" />
                      RCA Cited
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1 text-[11px] font-mono text-slate-400 flex-wrap">
                  <span>Type: <strong className="text-slate-300">{primary.issue_type}</strong></span>
                  <span>·</span>
                  <span>Status: <strong className="text-emerald-400">{primary.status}</strong></span>
                  <span>·</span>
                  <span>Priority: <strong className="text-amber-300">{primary.priority}</strong></span>
                  {primary.assignee && (
                    <>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-500" />
                        {primary.assignee}
                      </span>
                    </>
                  )}
                  {primary.updated && (
                    <>
                      <span>·</span>
                      <span className="flex items-center gap-1 text-slate-500">
                        <Clock className="w-3 h-3" />
                        {new Date(primary.updated).toLocaleDateString()}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {primary.url && (
              <a
                href={primary.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 transition-colors p-1.5 rounded hover:bg-slate-900 border border-slate-800 text-xs font-mono flex items-center gap-1 shrink-0 self-start sm:self-auto"
                title="View issue in Jira"
              >
                <span>View Issue</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>

          {/* Description preview */}
          {primary.description && (
            <p className="text-xs text-slate-400 font-sans line-clamp-3 bg-slate-900/60 p-2.5 rounded border border-slate-800/80 whitespace-pre-wrap">
              {primary.description}
            </p>
          )}

          {/* Correlation Match Badges */}
          {evidence.correlation && evidence.correlation.matched_by.length > 0 && (
            <div className="flex items-center gap-2 pt-1 border-t border-slate-800/60 flex-wrap">
              <span className="text-[10px] font-mono text-slate-500 uppercase">Match Signals:</span>
              {evidence.correlation.matched_by.map((sig) => (
                <span
                  key={sig}
                  className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-slate-300 border border-slate-800 flex items-center gap-1"
                >
                  <Tag className="w-2.5 h-2.5 text-sky-400" />
                  {sig}
                </span>
              ))}
              {primary.labels && primary.labels.length > 0 && (
                primary.labels.map((lbl) => (
                  <span
                    key={lbl}
                    className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-slate-400 border border-slate-800/60"
                  >
                    #{lbl}
                  </span>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Additional Matched Issues List */}
      {evidence.matched_issues.length > 1 && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 font-semibold">
            <Layers className="w-3.5 h-3.5 text-sky-400" />
            <span>Additional Correlated Work Items ({evidence.matched_issues.length - 1})</span>
          </div>

          <div className="bg-slate-950 rounded border border-slate-800 divide-y divide-slate-800/60 font-mono text-xs">
            {evidence.matched_issues.slice(1).map((issue) => {
              const isExpanded = expandedIssueKey === issue.key;
              const cited = isIssueCitedInRCA(issue);

              return (
                <div
                  key={issue.key}
                  className={`p-3 space-y-2 hover:bg-slate-900/30 transition-colors ${
                    cited ? 'border-l-2 border-l-sky-500 bg-sky-950/10' : ''
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-start gap-2 min-w-0">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-900 text-sky-400 border border-slate-800 shrink-0">
                        {issue.key}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-100 font-semibold block truncate" title={issue.summary}>
                            {issue.summary}
                          </span>
                          {cited && (
                            <span className="text-[10px] font-mono px-1 py-0.1 rounded bg-sky-500/20 text-sky-300 border border-sky-500/40">
                              Cited
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-400 block mt-0.5">
                          {issue.issue_type} · Status: <span className="text-emerald-400">{issue.status}</span> · Priority: {issue.priority}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                      {issue.url && (
                        <a
                          href={issue.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sky-400 hover:text-sky-300 transition-colors p-1"
                          title="Open in Jira"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      <button
                        onClick={() => setExpandedIssueKey(isExpanded ? null : issue.key)}
                        className="text-slate-400 hover:text-slate-200 transition-colors p-1"
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {isExpanded && issue.description && (
                    <div className="bg-slate-900/80 p-2.5 rounded border border-slate-800 text-[11px] font-sans text-slate-300">
                      <span className="text-[10px] uppercase text-slate-500 font-mono font-semibold block mb-1">
                        Issue Description
                      </span>
                      <p className="whitespace-pre-wrap">{issue.description}</p>
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
