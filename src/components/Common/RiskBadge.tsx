import React from 'react';
import { RiskLevel } from '@/types';

interface RiskBadgeProps {
  risk: RiskLevel;
  score?: number;
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ risk, score, showScore = false }) => {
  const styles: Record<RiskLevel, { bg: string; text: string; border: string }> = {
    CRITICAL: {
      bg: 'bg-red-50 dark:bg-red-950/40',
      text: 'text-red-700 dark:text-red-300',
      border: 'border-red-200 dark:border-red-900/60',
    },
    VERY_HIGH: {
      bg: 'bg-red-50 dark:bg-red-950/40',
      text: 'text-red-700 dark:text-red-300',
      border: 'border-red-200 dark:border-red-900/60',
    },
    HIGH: {
      bg: 'bg-orange-50 dark:bg-orange-950/40',
      text: 'text-orange-700 dark:text-orange-300',
      border: 'border-orange-200 dark:border-orange-900/60',
    },
    MEDIUM: {
      bg: 'bg-amber-50 dark:bg-amber-950/40',
      text: 'text-amber-700 dark:text-amber-300',
      border: 'border-amber-200 dark:border-amber-900/60',
    },
    LOW: {
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      text: 'text-emerald-700 dark:text-emerald-300',
      border: 'border-emerald-200 dark:border-emerald-900/60',
    },
  };

  const style = styles[risk] || styles.LOW;
  const label = risk === 'VERY_HIGH' ? 'VERY HIGH' : risk;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-sans font-medium border ${style.bg} ${style.text} ${style.border}`}
    >
      <span>{label}</span>
      {showScore && score !== undefined && (
        <span className="opacity-75 text-[11px] font-semibold pl-1 border-l border-current/30">
          {score}/100
        </span>
      )}
    </span>
  );
};
