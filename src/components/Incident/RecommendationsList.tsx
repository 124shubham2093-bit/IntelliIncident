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
        return 'text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/60';
      case 'HIGH':
        return 'text-orange-700 dark:text-orange-300 bg-orange-50 dark:bg-orange-950/40 border-orange-200 dark:border-orange-900/60';
      case 'MEDIUM':
        return 'text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60';
      default:
        return 'text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900/60';
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Recommended Actions
        </h3>
        <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
          {recommendations.length} Actions
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {recommendations.map((rec, idx) => (
          <div
            key={rec.id}
            className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-4 hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      #{idx + 1}
                    </span>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{rec.title}</h4>
                  </div>
                  <p className="mt-1 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    {rec.description}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${getPriorityBadge(
                    rec.priority
                  )}`}
                >
                  {rec.priority} Priority
                </span>
                <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700 shadow-2xs">
                  {rec.category}
                </span>
              </div>
            </div>

            {rec.actionCmd && (
              <div className="mt-3 bg-slate-900 dark:bg-slate-950 rounded-md p-2.5 flex items-center justify-between text-xs font-mono text-slate-200 border dark:border-slate-800">
                <div className="flex items-center gap-2 overflow-x-auto">
                  <Terminal className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <code>{rec.actionCmd}</code>
                </div>
                <button
                  type="button"
                  onClick={() => navigator.clipboard?.writeText(rec.actionCmd || '')}
                  className="ml-2 text-[11px] text-slate-300 hover:text-white px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 shrink-0 cursor-pointer"
                  title="Copy command to clipboard"
                >
                  Copy
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
