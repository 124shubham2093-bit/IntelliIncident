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
      bg: 'bg-rose-500/15',
      text: 'text-rose-400',
      border: 'border-rose-500/40',
    },
    VERY_HIGH: {
      bg: 'bg-red-500/15',
      text: 'text-red-400',
      border: 'border-red-500/40',
    },
    HIGH: {
      bg: 'bg-orange-500/15',
      text: 'text-orange-400',
      border: 'border-orange-500/40',
    },
    MEDIUM: {
      bg: 'bg-amber-500/15',
      text: 'text-amber-400',
      border: 'border-amber-500/40',
    },
    LOW: {
      bg: 'bg-blue-500/15',
      text: 'text-blue-400',
      border: 'border-blue-500/40',
    },
  };

  const style = styles[risk] || styles.LOW;
  const label = risk === 'VERY_HIGH' ? 'VERY HIGH' : risk;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border ${style.bg} ${style.text} ${style.border}`}
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
