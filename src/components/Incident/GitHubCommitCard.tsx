import React, { useState } from 'react';
import {
  GitCommit,
  ExternalLink,
  FileCode,
  Check,
  Copy,
  Plus,
  Minus,
  FileDiff,
  User,
  Calendar,
} from 'lucide-react';
import { GitHubCommitDetail, RootCauseCandidate } from '@/types';

interface GitHubCommitCardProps {
  commit: GitHubCommitDetail;
  rootCauseCandidates?: RootCauseCandidate[];
}

export const GitHubCommitCard: React.FC<GitHubCommitCardProps> = ({
  commit,
  rootCauseCandidates = [],
}) => {
  const [copiedSha, setCopiedSha] = useState(false);

  const handleCopySha = (sha: string) => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(sha);
      setCopiedSha(true);
      setTimeout(() => setCopiedSha(false), 2000);
    }
  };

  const isReferencedInRCA = (filename: string): boolean => {
    if (!rootCauseCandidates || rootCauseCandidates.length === 0) return false;
    const baseName = filename.split('/').pop() || filename;
    return rootCauseCandidates.some((candidate) =>
      candidate.evidence.some(
        (ev) =>
          ev.includes(`references '${filename}'`) ||
          (baseName.length >= 4 && ev.includes(`references '${baseName}'`))
      )
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'added':
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
            added
          </span>
        );
      case 'removed':
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-900/60">
            removed
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900/60">
            modified
          </span>
        );
    }
  };

  const commitDate = commit.committed_at || commit.author?.date;
  const formattedDate = commitDate
    ? new Date(commitDate).toISOString().replace('T', ' ').substring(0, 19) + ' UTC'
    : null;

  return (
    <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-5 space-y-4 hover:border-slate-300 dark:hover:border-slate-600 transition-colors">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-2xs shrink-0">
            <GitCommit className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                Correlated Deployment Commit
              </span>
              <span className="text-xs font-mono font-semibold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/40 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-900/60">
                {commit.short_sha}
              </span>
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Code Change Evidence
            </span>
          </div>
        </div>

        {/* Actions: Copy SHA & External View */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => handleCopySha(commit.sha)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 text-xs font-medium transition-colors shadow-2xs cursor-pointer"
            title="Copy full commit SHA"
          >
            {copiedSha ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span className="text-emerald-700 dark:text-emerald-300">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>SHA</span>
              </>
            )}
          </button>

          {commit.html_url && (
            <a
              href={commit.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-blue-700 dark:text-blue-400 border border-slate-300 dark:border-slate-700 text-xs font-medium transition-colors shadow-2xs"
            >
              <span>View on GitHub</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* Commit Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        {/* Message */}
        <div className="md:col-span-2 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-md p-3 space-y-1">
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider block">
            Commit Message
          </span>
          <p className="text-slate-800 dark:text-slate-200 text-xs leading-relaxed line-clamp-2">
            {commit.message}
          </p>
        </div>

        {/* Author & Timestamp */}
        <div className="bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-md p-3 space-y-2">
          <div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider block">Author</span>
            <div className="flex items-center gap-1.5 mt-0.5 text-slate-800 dark:text-slate-200">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span className="truncate font-medium">
                {commit.author?.name || 'Unknown Author'}
                {commit.author?.username ? ` (@${commit.author.username})` : ''}
              </span>
            </div>
          </div>
          {formattedDate && (
            <div>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider block">Committed</span>
              <div className="flex items-center gap-1.5 mt-0.5 text-slate-600 dark:text-slate-400 text-[11px]">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>{formattedDate}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Diff Statistics Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white dark:bg-slate-800/80 rounded-md border border-slate-200 dark:border-slate-700 text-xs">
        <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
          <FileDiff className="w-4 h-4 text-slate-400" />
          <span>Files Changed:</span>
          <span className="font-bold text-slate-900 dark:text-slate-100">{commit.files.length}</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-semibold">
            <Plus className="w-3.5 h-3.5" />
            <span>{commit.stats?.additions ?? 0} additions</span>
          </div>

          <div className="flex items-center gap-1 text-red-600 dark:text-red-400 font-semibold">
            <Minus className="w-3.5 h-3.5" />
            <span>{commit.stats?.deletions ?? 0} deletions</span>
          </div>
        </div>
      </div>

      {/* Changed Files List */}
      {commit.files && commit.files.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider block">
            Changed Files in Release:
          </span>

          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {commit.files.map((file) => {
              const citedInTrace = isReferencedInRCA(file.filename);
              return (
                <div
                  key={file.filename}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2 rounded-md text-xs border transition-colors ${
                    citedInTrace
                      ? 'bg-blue-50/70 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900/60'
                      : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {getStatusBadge(file.status)}
                    {file.blob_url ? (
                      <a
                        href={file.blob_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-800 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-400 transition-colors truncate flex items-center gap-1 font-mono text-xs"
                      >
                        <span className="truncate">{file.filename}</span>
                        <ExternalLink className="w-3 h-3 text-slate-400 shrink-0" />
                      </a>
                    ) : (
                      <span className="text-slate-800 dark:text-slate-200 truncate font-mono text-xs">{file.filename}</span>
                    )}

                    {citedInTrace && (
                      <span className="text-[10px] text-blue-700 dark:text-blue-300 bg-blue-100/70 dark:bg-blue-950/60 px-1.5 py-0.5 rounded border border-blue-200 dark:border-blue-800 flex items-center gap-1 shrink-0 font-medium">
                        <FileCode className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                        Referenced in Stack Trace
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto text-xs font-mono">
                    <span className="text-emerald-700 dark:text-emerald-400 font-semibold">+{file.additions}</span>
                    <span className="text-red-600 dark:text-red-400 font-semibold">-{file.deletions}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
