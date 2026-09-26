import React from 'react';

interface DemoBadgeProps {
  label?: string;
  className?: string;
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  label = 'DEMO DATA — BACKEND PENDING',
  className = '',
}) => {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide uppercase bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
      title="This component is displaying demonstration telemetry until the FastAPI backend is operational."
    >
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
      {label}
    </span>
  );
};
