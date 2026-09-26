import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  ArrowUpDown,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { getIncidents } from '@/api/incidents';
import { Incident } from '@/types';

export const IncidentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [search, setSearch] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedRisk, setSelectedRisk] = useState('ALL');
  const [selectedService, setSelectedService] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await getIncidents({
        search,
        severity: selectedSeverity,
        risk: selectedRisk,
        service: selectedService,
        status: selectedStatus,
      });
      setIncidents(res.data);
      setLoading(false);
    }
    loadData();
  }, [search, selectedSeverity, selectedRisk, selectedService, selectedStatus]);

  const serviceOptions = useMemo(() => {
    return [
      'ALL',
      'payment-gateway',
      'checkout-api',
      'auth-service',
      'inventory-service',
      'search-indexer',
      'notification-worker',
    ];
  }, []);

  const resetFilters = () => {
    setSearch('');
    setSelectedSeverity('ALL');
    setSelectedRisk('ALL');
    setSelectedService('ALL');
    setSelectedStatus('ALL');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
            Incident Management
          </h1>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span>Total Records:</span>
          <span className="font-bold text-slate-200 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            {incidents.length}
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
          {/* Search input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by incident ID, summary title, or microservice..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-md text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500/60 focus:ring-1 focus:ring-teal-500/40"
            />
          </div>

          {/* Quick Clear Button */}
          {(search ||
            selectedSeverity !== 'ALL' ||
            selectedRisk !== 'ALL' ||
            selectedService !== 'ALL' ||
            selectedStatus !== 'ALL') && (
            <button
              type="button"
              onClick={resetFilters}
              className="flex items-center gap-1.5 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* Filter Dropdowns Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-800/80 text-xs font-mono">
          {/* Severity */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
              Severity
            </label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500/60"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* Risk */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
              Fuzzy Risk
            </label>
            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500/60"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* Service */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
              Service
            </label>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500/60"
            >
              {serviceOptions.map((svc) => (
                <option key={svc} value={svc}>
                  {svc === 'ALL' ? 'All Services' : svc}
                </option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider block mb-1">
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500/60"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="MITIGATED">Mitigated</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-12 text-center text-xs font-mono text-slate-400">Loading incidents...</div>
          ) : incidents.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-slate-400">
              No incidents matching the active filter criteria.
            </div>
          ) : (
            <table className="w-full text-left border-collapse font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider bg-slate-950/60">
                  <th className="py-3 px-4">
                    <span className="flex items-center gap-1">
                      Incident ID <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </span>
                  </th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Title / Summary</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Risk</th>
                  <th className="py-3 px-4">Anomaly</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {incidents.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => navigate(`/incidents/${inc.id}`)}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-4 font-bold text-teal-400 group-hover:underline">
                      {inc.id}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {new Date(inc.timestamp).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric',
                      })}{' '}
                      {new Date(inc.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3.5 px-4 text-slate-200 font-sans font-medium">
                      {inc.service}
                    </td>
                    <td className="py-3.5 px-4 font-sans text-slate-300 max-w-xs truncate">
                      {inc.title}
                    </td>
                    <td className="py-3.5 px-4">
                      <SeverityBadge severity={inc.severity} size="sm" />
                    </td>
                    <td className="py-3.5 px-4">
                      <RiskBadge risk={inc.risk} score={inc.riskScore} showScore />
                    </td>
                    <td className="py-3.5 px-4">
                      {inc.anomalyDetected ? (
                        <span className="inline-flex items-center gap-1.5 text-[11px] text-rose-400 font-semibold">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
                          Anomaly ({(inc.anomalyScore).toFixed(2)})
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400">Normal</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="inline-flex items-center gap-1 text-teal-400 group-hover:text-teal-300 font-medium">
                        Investigate <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="p-3 bg-slate-950/60 border-t border-slate-800 text-[11px] font-mono text-slate-400 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <span>Total {incidents.length} active operational incidents tracked</span>
          <span className="text-teal-400">Stream Status: Synchronized</span>
        </div>
      </div>
    </div>
  );
};
