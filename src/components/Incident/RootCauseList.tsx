import React from 'react';
import { GitCommit, Database, Cpu, Network, FileWarning, ArrowUpRight } from 'lucide-react';
import { RootCauseCandidate } from '@/types';

interface RootCauseListProps {
  candidates: RootCauseCandidate[];
}

export const RootCauseList: React.FC<RootCauseListProps> = ({ candidates }) => {
  const getCategoryIcon = (category: RootCauseCandidate['category']) => {
    switch (category) {
      case 'DEPLOYMENT':
        return <GitCommit className="w-4 h-4 text-cyan-400" />;
      case 'DATABASE':
        return <Database className="w-4 h-4 text-emerald-400" />;
      case 'INFRASTRUCTURE':
        return <Cpu className="w-4 h-4 text-amber-400" />;
      case 'NETWORK':
        return <Network className="w-4 h-4 text-indigo-400" />;
      default:
        return <FileWarning className="w-4 h-4 text-rose-400" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    if (score >= 0.5) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 0.8) return 'bg-rose-500';
    if (score >= 0.5) return 'bg-amber-500';
    return 'bg-blue-500';
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono">
          Ranked Root Cause Candidates
        </h3>
        <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
          {candidates.length} Hypotheses
        </span>
      </div>

      <div className="mt-3 p-2 rounded bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 font-mono flex items-center justify-between">
        <span>Causal attribution computed via temporal correlation & dependency graph inference</span>
        <span className="text-teal-400">Correlation Engine</span>
      </div>

      <div className="mt-4 space-y-4">
        {candidates.map((rc, idx) => {
          const scorePercent = Math.round(rc.score * 100);
          return (
            <div
              key={rc.id}
              className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-6 h-6 rounded bg-slate-900 text-slate-400 font-mono text-xs font-semibold border border-slate-800">
                    #{idx + 1}
                  </div>
                  <div className="p-1.5 rounded bg-slate-900 border border-slate-800">
                    {getCategoryIcon(rc.category)}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100 font-mono">
                      {rc.candidate}
                    </h4>
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wide">
                      Category: {rc.category}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <div className="w-28 text-right">
                    <div className="flex items-center justify-between text-xs font-mono mb-1">
                      <span className="text-slate-400 text-[10px]">Causal Score</span>
                      <span className="font-bold text-slate-200">{(rc.score).toFixed(2)}</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${getProgressBarColor(rc.score)}`}
                        style={{ width: `${scorePercent}%` }}
                      />
                    </div>
                  </div>
                  <span
                    className={`text-xs font-mono font-bold px-2 py-1 rounded border ${getScoreColor(
                      rc.score
                    )}`}
                  >
                    {scorePercent}%
                  </span>
                </div>
              </div>

              {/* Explanation */}
              <div className="mt-3 text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                <span className="font-mono text-teal-400 font-semibold mr-1.5">Hypothesis:</span>
                {rc.explanation}
              </div>

              {/* Evidence list */}
              {rc.evidence && rc.evidence.length > 0 && (
                <div className="mt-3">
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                    Supporting Evidence:
                  </span>
                  <ul className="space-y-1">
                    {rc.evidence.map((item, eIdx) => (
                      <li
                        key={eIdx}
                        className="text-xs text-slate-300 flex items-start gap-2 font-mono"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                        <span>{item}</span>
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
