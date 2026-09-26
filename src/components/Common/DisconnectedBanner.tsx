import React from 'react';
import { AlertTriangle, ServerOff } from 'lucide-react';
import { API_BASE_URL } from '@/api/client';

interface DisconnectedBannerProps {
  className?: string;
  backendUrl?: string;
}

export const DisconnectedBanner: React.FC<DisconnectedBannerProps> = ({
  className = '',
  backendUrl = API_BASE_URL,
}) => {
  return (
    <div
      className={`bg-amber-950/30 border border-amber-500/30 rounded-lg p-3.5 flex items-start gap-3 text-amber-200 text-xs ${className}`}
    >
      <div className="p-1 rounded bg-amber-500/20 text-amber-400 mt-0.5">
        <ServerOff className="w-4 h-4" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold tracking-wide uppercase font-mono text-[11px] text-amber-300">
            Frontend Operating in Demo Mode
          </span>
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-amber-500/20 text-amber-300">
            Backend Disconnected
          </span>
        </div>
        <p className="mt-1 text-slate-300 leading-relaxed">
          FastAPI backend endpoint at <code className="font-mono text-amber-300/90">{backendUrl}</code> is not connected. All operational metrics, ML predictions, and fuzzy risk assessments are rendered using offline demonstration fixtures. Backend services will be connected in subsequent phases.
        </p>
      </div>
      <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-amber-500/20 text-[11px] font-mono text-amber-400">
        <AlertTriangle className="w-3.5 h-3.5" />
        <span>UI Review Only</span>
      </div>
    </div>
  );
};
