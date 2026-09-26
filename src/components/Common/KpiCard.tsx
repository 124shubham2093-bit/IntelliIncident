import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  accentColor?: 'teal' | 'rose' | 'amber' | 'blue';
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  accentColor = 'teal',
}) => {
  const accentBorder = {
    teal: 'border-l-teal-500',
    rose: 'border-l-rose-500',
    amber: 'border-l-amber-500',
    blue: 'border-l-blue-500',
  }[accentColor];

  const iconBg = {
    teal: 'bg-teal-500/10 text-teal-400',
    rose: 'bg-rose-500/10 text-rose-400',
    amber: 'bg-amber-500/10 text-amber-400',
    blue: 'bg-blue-500/10 text-blue-400',
  }[accentColor];

  return (
    <div
      className={`bg-slate-900/80 border border-slate-800 rounded-lg p-5 border-l-4 ${accentBorder} shadow-sm relative overflow-hidden`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-slate-100 tracking-tight">
              {value}
            </span>
            {trend && (
              <span
                className={`text-xs font-mono font-medium ${
                  trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {trend.value}
              </span>
            )}
          </div>
          {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-md ${iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {trend?.label && (
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
          <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            {trend.label}
          </span>
          <span className="text-[10px] font-mono text-slate-500">Telemetry Active</span>
        </div>
      )}
    </div>
  );
};
