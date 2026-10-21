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
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Connected & Correlated</span>
          </span>
        );
      case 'NO_ISSUES_FOUND':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            <span>0 Correlated Issues</span>
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
            <span>Jira Offline</span>
          </span>
        );
      case 'AUTH_ERROR':
        return (
          <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
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
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Ticket className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-900">
            Jira Work Item & Ticket Correlation
          </h3>
          {evidence.project_key && (
            <span className="text-xs text-slate-500 hidden md:inline">
              (Project: {evidence.project_key})
            </span>
          )}
        </div>
        <div>{getStatusBadge(evidence.status)}</div>
      </div>

      {/* Overview Metadata Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Matched Ticket</span>
          <span className="font-mono text-blue-700 font-bold text-sm block mt-0.5 truncate">
            {primary ? primary.key : 'None'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Match Confidence</span>
          <span
            className={`font-semibold block mt-0.5 truncate ${
              evidence.correlation_strength === 'HIGH'
                ? 'text-emerald-700 font-bold'
                : evidence.correlation_strength === 'MEDIUM'
                ? 'text-amber-700'
                : evidence.correlation_strength === 'LOW'
                ? 'text-blue-700'
                : 'text-slate-500'
            }`}
          >
            {evidence.correlation
              ? `${Math.round(evidence.correlation.confidence_score * 100)}% (${evidence.correlation_strength})`
              : 'N/A'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Jira Server</span>
          <span className="text-slate-800 font-mono text-[11px] font-medium block mt-0.5 truncate" title={evidence.base_url}>
            {evidence.base_url ? evidence.base_url.replace(/^https?:\/\//, '') : 'None'}
          </span>
        </div>
        <div className="bg-white p-3 rounded-md border border-slate-200">
          <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider block">Matched Candidates</span>
          <span className="text-slate-800 font-semibold block mt-0.5">
            {evidence.matched_issues.length} candidate(s)
          </span>
        </div>
      </div>

      {/* Diagnostic Message */}
      <p className="text-xs text-slate-700 bg-white p-3 rounded-md border border-slate-200 leading-relaxed">
        {evidence.summary}
      </p>

      {/* Primary Correlated Ticket Details */}
      {primary && (
        <div
          className={`bg-white rounded-lg border border-slate-200 p-4 space-y-3 ${
            isPrimaryCited ? 'border-l-4 border-l-blue-600' : ''
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-start gap-2.5 min-w-0">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 shrink-0">
                {primary.key}
              </span>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-xs sm:text-sm font-semibold text-slate-900">{primary.summary}</h4>
                  {isPrimaryCited && (
                    <span className="text-[11px] px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1 font-medium">
                      <BookmarkCheck className="w-3.5 h-3.5 text-blue-600" />
                      RCA Cited
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-500 flex-wrap">
                  <span>Type: <strong className="text-slate-700 font-medium">{primary.issue_type}</strong></span>
                  <span>&bull;</span>
                  <span>Status: <strong className="text-emerald-700 font-medium">{primary.status}</strong></span>
                  <span>&bull;</span>
                  <span>Priority: <strong className="text-amber-800 font-medium">{primary.priority}</strong></span>
                  {primary.assignee && (
                    <>
                      <span>&bull;</span>
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-400" />
                        {primary.assignee}
                      </span>
                    </>
                  )}
                  {primary.updated && (
                    <>
                      <span>&bull;</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
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
                className="text-blue-700 hover:text-blue-800 bg-white hover:bg-slate-50 border border-slate-300 p-1.5 rounded-md text-xs font-medium flex items-center gap-1 shrink-0 self-start sm:self-auto shadow-2xs"
                title="View issue in Jira"
              >
                <span>View Issue</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>

          {/* Description preview */}
          {primary.description && (
            <p className="text-xs text-slate-600 line-clamp-3 bg-slate-50 p-3 rounded-md border border-slate-200 whitespace-pre-wrap leading-relaxed">
              {primary.description}
            </p>
          )}

          {/* Correlation Match Badges */}
          {evidence.correlation && evidence.correlation.matched_by.length > 0 && (
            <div className="flex items-center gap-2 pt-2 border-t border-slate-100 flex-wrap text-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Signals:</span>
              {evidence.correlation.matched_by.map((sig) => (
                <span
                  key={sig}
                  className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1"
                >
                  <Tag className="w-2.5 h-2.5 text-blue-600" />
                  {sig}
                </span>
              ))}
              {primary.labels && primary.labels.length > 0 && (
                primary.labels.map((lbl) => (
                  <span
                    key={lbl}
                    className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-mono"
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
          <div className="flex items-center gap-1.5 text-xs text-slate-800 font-semibold">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            <span>Additional Correlated Work Items ({evidence.matched_issues.length - 1})</span>
          </div>

          <div className="bg-white rounded-md border border-slate-200 divide-y divide-slate-100 text-xs">
            {evidence.matched_issues.slice(1).map((issue) => {
              const isExpanded = expandedIssueKey === issue.key;
              const cited = isIssueCitedInRCA(issue);

              return (
                <div
                  key={issue.key}
                  className={`p-3 space-y-2 hover:bg-slate-50 transition-colors ${
                    cited ? 'border-l-2 border-l-blue-600 bg-blue-50/30' : ''
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-start gap-2 min-w-0">
                      <span className="text-xs font-mono font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-blue-700 border border-slate-200 shrink-0">
                        {issue.key}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-800 font-semibold block truncate" title={issue.summary}>
                            {issue.summary}
                          </span>
                          {cited && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-100 text-blue-800 border border-blue-200 font-medium">
                              Cited
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-500 block mt-0.5">
                          {issue.issue_type} &bull; Status: <span className="text-emerald-700 font-medium">{issue.status}</span> &bull; Priority: {issue.priority}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                      {issue.url && (
                        <a
                          href={issue.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 transition-colors p-1"
                          title="Open in Jira"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                      <button
                        onClick={() => setExpandedIssueKey(isExpanded ? null : issue.key)}
                        className="text-slate-400 hover:text-slate-600 transition-colors p-1"
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {isExpanded && issue.description && (
                    <div className="bg-slate-50 p-3 rounded border border-slate-200 text-xs text-slate-700">
                      <span className="text-[11px] uppercase text-slate-500 font-semibold block mb-1">
                        Issue Description
                      </span>
                      <p className="whitespace-pre-wrap leading-relaxed">{issue.description}</p>
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
