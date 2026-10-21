import React from 'react';
import { GitCommit, Database, Cpu, Network, FileWarning } from 'lucide-react';
import { RootCauseCandidate } from '@/types';

interface RootCauseListProps {
  candidates: RootCauseCandidate[];
}

export const RootCauseList: React.FC<RootCauseListProps> = ({ candidates }) => {
  const getCategoryIcon = (category: RootCauseCandidate['category']) => {
    switch (category) {
      case 'DEPLOYMENT':
        return <GitCommit className="w-4 h-4 text-blue-600 dark:text-blue-400" />;
      case 'DATABASE':
        return <Database className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />;
      case 'INFRASTRUCTURE':
        return <Cpu className="w-4 h-4 text-amber-600 dark:text-amber-400" />;
      case 'NETWORK':
        return <Network className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />;
      default:
        return <FileWarning className="w-4 h-4 text-red-600 dark:text-red-400" />;
    }
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return 'text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/60';
    if (score >= 0.5) return 'text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60';
    return 'text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900/60';
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 0.8) return 'bg-red-600';
    if (score >= 0.5) return 'bg-amber-500';
    return 'bg-blue-600';
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Ranked Root Cause Hypotheses
        </h3>
        <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
          {candidates.length} Hypotheses
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {candidates.map((rc, idx) => {
          const scorePercent = Math.round(rc.score * 100);
          return (
            <div
              key={rc.id}
              className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-6 h-6 rounded-md bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-semibold text-xs border border-slate-200 dark:border-slate-700 shadow-2xs">
                    #{idx + 1}
                  </div>
                  <div className="p-1.5 rounded-md bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-2xs">
                    {getCategoryIcon(rc.category)}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {rc.candidate}
                    </h4>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                      Category: {rc.category}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <div className="w-28 text-right">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-500 dark:text-slate-400 text-[11px]">Score</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{(rc.score).toFixed(2)}</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${getProgressBarColor(rc.score)}`}
                        style={{ width: `${scorePercent}%` }}
                      />
                    </div>
                  </div>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${getScoreBadge(
                      rc.score
                    )}`}
                  >
                    {scorePercent}%
                  </span>
                </div>
              </div>

              <p className="mt-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {rc.explanation}
              </p>

              {rc.evidence && rc.evidence.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-slate-200/70 dark:border-slate-700/80">
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                    Correlated Evidence:
                  </span>
                  <ul className="space-y-1">
                    {rc.evidence.map((ev, i) => (
                      <li key={i} className="text-xs text-slate-600 dark:text-slate-300 flex items-start gap-1.5">
                        <span className="text-slate-400 dark:text-slate-500 mt-0.5">&bull;</span>
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
