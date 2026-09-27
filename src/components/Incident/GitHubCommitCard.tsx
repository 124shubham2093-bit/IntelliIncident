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

  // Deterministically verify if a changed file was cited in backend RCA evidence
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
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            added
          </span>
        );
      case 'removed':
        return (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
            removed
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
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
    <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-5 space-y-4 hover:border-slate-700 transition-colors">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 shrink-0">
            <GitCommit className="w-4 h-4 text-teal-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                Correlated Deployment Commit
              </span>
              <span className="text-[10px] font-mono text-teal-400 bg-teal-500/10 px-1.5 py-0.5 rounded border border-teal-500/30">
                {commit.short_sha}
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Code Change Evidence
            </span>
          </div>
        </div>

        {/* Actions: Copy SHA & External View */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => handleCopySha(commit.sha)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-mono transition-colors cursor-pointer"
            title="Copy full commit SHA"
          >
            {copiedSha ? (
              <>
                <Check className="w-3.5 h-3.5 text-teal-400" />
                <span className="text-teal-400">Copied</span>
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
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 text-xs font-mono font-medium transition-colors"
            >
              <span>View on GitHub</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* Commit Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
        {/* Message */}
        <div className="md:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded p-3 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
            Commit Message
          </span>
          <p className="text-slate-100 font-sans text-xs leading-relaxed line-clamp-2">
            {commit.message}
          </p>
        </div>

        {/* Author & Timestamp */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded p-3 space-y-2">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Author</span>
            <div className="flex items-center gap-1.5 mt-0.5 text-slate-200">
              <User className="w-3 h-3 text-slate-400" />
              <span className="truncate">
                {commit.author?.name || 'Unknown Author'}
                {commit.author?.username ? ` (@${commit.author.username})` : ''}
              </span>
            </div>
          </div>
          {formattedDate && (
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Committed</span>
              <div className="flex items-center gap-1.5 mt-0.5 text-slate-300 text-[11px]">
                <Calendar className="w-3 h-3 text-slate-400" />
                <span>{formattedDate}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Diff Statistics Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/40 rounded border border-slate-800/60 text-xs font-mono">
        <div className="flex items-center gap-2 text-slate-300">
          <FileDiff className="w-4 h-4 text-slate-400" />
          <span>Files Changed:</span>
          <span className="font-bold text-slate-100">{commit.files.length}</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-emerald-400">
            <Plus className="w-3.5 h-3.5" />
            <span className="font-bold">{commit.stats?.additions ?? 0}</span>
            <span className="text-[10px] text-slate-400">additions</span>
          </div>

          <div className="flex items-center gap-1 text-rose-400">
            <Minus className="w-3.5 h-3.5" />
            <span className="font-bold">{commit.stats?.deletions ?? 0}</span>
            <span className="text-[10px] text-slate-400">deletions</span>
          </div>
        </div>
      </div>

      {/* Changed Files List */}
      {commit.files && commit.files.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
            Changed Files in Release:
          </span>

          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {commit.files.map((file) => {
              const citedInTrace = isReferencedInRCA(file.filename);
              return (
                <div
                  key={file.filename}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2 rounded text-xs font-mono border transition-colors ${
                    citedInTrace
                      ? 'bg-cyan-500/10 border-cyan-500/30'
                      : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {getStatusBadge(file.status)}
                    {file.blob_url ? (
                      <a
                        href={file.blob_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-200 hover:text-teal-300 transition-colors truncate flex items-center gap-1"
                      >
                        <span className="truncate">{file.filename}</span>
                        <ExternalLink className="w-3 h-3 text-slate-500 shrink-0" />
                      </a>
                    ) : (
                      <span className="text-slate-200 truncate">{file.filename}</span>
                    )}

                    {citedInTrace && (
                      <span className="text-[10px] font-mono text-cyan-300 bg-cyan-500/20 px-1.5 py-0.5 rounded border border-cyan-500/40 flex items-center gap-1 shrink-0">
                        <FileCode className="w-3 h-3 text-cyan-400" />
                        Referenced in Stack Trace
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto text-[11px]">
                    <span className="text-emerald-400 font-medium">+{file.additions}</span>
                    <span className="text-rose-400 font-medium">-{file.deletions}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Footer Citation Contract */}
      <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-400">
        <span>Empirical change evidence &bull; Correlated with incident release window</span>
        <span className="text-teal-400">GitHub Intelligence</span>
      </div>
    </div>
  );
};
