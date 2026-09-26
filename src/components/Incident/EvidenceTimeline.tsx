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
        return <Rocket className="w-4 h-4 text-cyan-400" />;
      case 'ERROR_SPIKE':
        return <AlertOctagon className="w-4 h-4 text-rose-400" />;
      case 'LATENCY_INCREASE':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'MONITORING_ALERT':
        return <BellRing className="w-4 h-4 text-orange-400" />;
      case 'SUPPORT_TICKET_SPIKE':
        return <MessageSquareWarning className="w-4 h-4 text-purple-400" />;
      case 'CONFIG_CHANGE':
        return <SlidersHorizontal className="w-4 h-4 text-indigo-400" />;
      default:
        return <Activity className="w-4 h-4 text-teal-400" />;
    }
  };

  const getEventBadgeClass = (type: EventType) => {
    switch (type) {
      case 'DEPLOYMENT':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'ERROR_SPIKE':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'LATENCY_INCREASE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'MONITORING_ALERT':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'SUPPORT_TICKET_SPIKE':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'CONFIG_CHANGE':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      default:
        return 'bg-teal-500/10 text-teal-400 border-teal-500/30';
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
    <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono">
            {title}
          </h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <span className="text-[11px] font-mono text-slate-400 self-start sm:self-auto bg-slate-800 px-2 py-0.5 rounded">
          {events.length} Telemetry Events
        </span>
      </div>

      <div className="mt-6 relative pl-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-px before:bg-slate-800">
        {events.map((event) => {
          const { time, date } = formatTimestamp(event.timestamp);
          return (
            <div key={event.id} className="relative pb-6 last:pb-0 group">
              {/* Dot / Icon on timeline line */}
              <div className="absolute -left-[30px] top-0.5 w-6 h-6 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center group-hover:border-slate-500 transition-colors">
                {getEventIcon(event.eventType)}
              </div>

              <div className="bg-slate-950/70 border border-slate-800/90 rounded-md p-3.5 hover:border-slate-700 transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${getEventBadgeClass(
                        event.eventType
                      )}`}
                    >
                      {event.eventType.replace('_', ' ')}
                    </span>
                    <span className="text-xs font-mono font-medium text-slate-300">
                      {event.service}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
                    <span>{date}</span>
                    <span className="text-slate-200 font-semibold">{time}</span>
                  </div>
                </div>

                <p className="mt-2 text-xs text-slate-300 leading-relaxed font-sans">
                  {event.description}
                </p>

                {event.metadata && Object.keys(event.metadata).length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex flex-wrap gap-2">
                    {Object.entries(event.metadata).map(([key, value]) => (
                      <span
                        key={key}
                        className="text-[10px] font-mono bg-slate-900 px-1.5 py-0.5 rounded text-slate-400 border border-slate-800"
                      >
                        <span className="text-slate-400">{key}:</span> {String(value)}
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
