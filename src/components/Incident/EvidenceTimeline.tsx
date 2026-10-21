import React from 'react';
import {
  Rocket,
  AlertOctagon,
  Clock,
  BellRing,
  MessageSquareWarning,
  SlidersHorizontal,
  Activity,
} from 'lucide-react';
import { EvidenceEvent, EventType } from '@/types';

interface EvidenceTimelineProps {
  events: EvidenceEvent[];
  title?: string;
  subtitle?: string;
}

export const EvidenceTimeline: React.FC<EvidenceTimelineProps> = ({
  events,
  title = 'Chronological Evidence Timeline',
  subtitle = 'Temporal correlation of operational deployment, telemetry shifts, and alert triggers.',
}) => {
  const getEventIcon = (type: EventType) => {
    switch (type) {
      case 'DEPLOYMENT':
        return <Rocket className="w-4 h-4 text-blue-600 dark:text-blue-400" />;
      case 'ERROR_SPIKE':
        return <AlertOctagon className="w-4 h-4 text-red-600 dark:text-red-400" />;
      case 'LATENCY_INCREASE':
        return <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400" />;
      case 'MONITORING_ALERT':
        return <BellRing className="w-4 h-4 text-orange-600 dark:text-orange-400" />;
      case 'SUPPORT_TICKET_SPIKE':
        return <MessageSquareWarning className="w-4 h-4 text-purple-600 dark:text-purple-400" />;
      case 'CONFIG_CHANGE':
        return <SlidersHorizontal className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />;
      default:
        return <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getEventBadgeClass = (type: EventType) => {
    switch (type) {
      case 'DEPLOYMENT':
        return 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-900/60';
      case 'ERROR_SPIKE':
        return 'bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-900/60';
      case 'LATENCY_INCREASE':
        return 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-900/60';
      case 'MONITORING_ALERT':
        return 'bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-900/60';
      case 'SUPPORT_TICKET_SPIKE':
        return 'bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-900/60';
      case 'CONFIG_CHANGE':
        return 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-900/60';
      default:
        return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
    }
  };

  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso);
      return {
        time: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        date: d.toLocaleDateString([], { month: 'short', day: 'numeric' }),
      };
    } catch {
      return { time: iso, date: '' };
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {title}
          </h3>
          {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400 self-start sm:self-auto bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
          {events.length} Telemetry Events
        </span>
      </div>

      <div className="mt-6 relative pl-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-slate-200 dark:before:bg-slate-800">
        {events.map((event) => {
          const { time, date } = formatTimestamp(event.timestamp);
          return (
            <div key={event.id} className="relative pb-6 last:pb-0 group">
              {/* Dot / Icon on timeline line */}
              <div className="absolute -left-[30px] top-0.5 w-6 h-6 rounded-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center shadow-xs">
                {getEventIcon(event.eventType)}
              </div>

              <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 rounded-lg p-3.5 hover:border-slate-300 dark:hover:border-slate-600 transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${getEventBadgeClass(
                        event.eventType
                      )}`}
                    >
                      {event.eventType.replace('_', ' ')}
                    </span>
                    <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">{event.service}</span>
                  </div>

                  <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5 font-mono">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>{date} {time}</span>
                  </div>
                </div>

                <p className="mt-2 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                  {event.description}
                </p>

                {event.metadata && Object.keys(event.metadata).length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200/60 dark:border-slate-700/80 flex flex-wrap gap-2 text-[11px]">
                    {Object.entries(event.metadata).map(([k, v]) => (
                      <span key={k} className="text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 font-mono">
                        <strong className="text-slate-800 dark:text-slate-200">{k}:</strong> {String(v)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
