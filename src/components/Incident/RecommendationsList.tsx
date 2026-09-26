import React from 'react';
import { CheckCircle2, Terminal } from 'lucide-react';
import { Recommendation } from '@/types';

interface RecommendationsListProps {
  recommendations: Recommendation[];
}

export const RecommendationsList: React.FC<RecommendationsListProps> = ({ recommendations }) => {
  const getPriorityBadge = (priority: Recommendation['priority']) => {
    switch (priority) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'HIGH':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      default:
        return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono">
          Recommended Investigation & Mitigation Actions
        </h3>
        <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
          {recommendations.length} Actions
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {recommendations.map((rec, idx) => (
          <div
            key={rec.id}
            className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-slate-400">
                      #{idx + 1}
                    </span>
                    <h4 className="text-sm font-semibold text-slate-100">{rec.title}</h4>
                  </div>
                  <p className="mt-1 text-xs text-slate-300 font-sans leading-relaxed">
                    {rec.description}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${getPriorityBadge(
                    rec.priority
                  )}`}
                >
                  {rec.priority}
                </span>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  {rec.category}
                </span>
              </div>
            </div>

            {rec.actionCmd && (
              <div className="mt-3 bg-black/60 rounded p-2.5 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 overflow-x-auto text-[11px] font-mono text-teal-300">
                  <Terminal className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <code>{rec.actionCmd}</code>
                </div>
                <button
                  type="button"
                  onClick={() => navigator.clipboard?.writeText(rec.actionCmd || '')}
                  className="ml-2 text-[10px] font-mono text-slate-400 hover:text-slate-200 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 shrink-0 cursor-pointer"
                  title="Copy command to clipboard"
                >
                  Copy
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
        <span>Remediation actions correlated from service operational playbooks</span>
        <span className="text-teal-400">Playbook Engine</span>
      </div>
    </div>
  );
};
