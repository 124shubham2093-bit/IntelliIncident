import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Flame,
  Activity,
  Gauge,
  TrendingUp,
  Server,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  CartesianGrid,
} from 'recharts';
import { useTheme } from '@/context/ThemeContext';
import { KpiCard } from '@/components/Common/KpiCard';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { getIncidents } from '@/api/incidents';
import { getDashboardChartData } from '@/api/analytics';
import { Incident } from '@/types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await getIncidents();
      setIncidents(res.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const chartData = useMemo(() => getDashboardChartData(incidents), [incidents]);

  const activeCount = incidents.filter((i) => i.status !== 'RESOLVED').length;
  const criticalCount = incidents.filter((i) => i.severity === 'CRITICAL').length;
  const anomaliesCount = incidents.filter((i) => i.anomalyDetected).length;
  const avgRisk = incidents.length > 0
    ? Math.round(incidents.reduce((acc, curr) => acc + curr.riskScore, 0) / incidents.length)
    : 0;

  const servicesList = useMemo(() => {
    if (incidents.length === 0) return [];
    const map: Record<string, { service: string; status: string; incidentsCount: number; maxSeverity: string; lastSeen: string }> = {};
    for (const inc of incidents) {
      if (!map[inc.service]) {
        map[inc.service] = {
          service: inc.service,
          status: inc.severity === 'CRITICAL' ? 'Degraded' : inc.severity === 'HIGH' ? 'Degraded' : 'Elevated',
          incidentsCount: 0,
          maxSeverity: inc.severity,
          lastSeen: inc.timestamp ? inc.timestamp.substring(11, 16) + ' UTC' : 'Recently',
        };
      }
      map[inc.service].incidentsCount += 1;
    }
    return Object.values(map);
  }, [incidents]);

  const isDark = theme === 'dark';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 font-sans">
            Operations Dashboard
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Real-time telemetry monitoring, ML anomaly detection, and incident response
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate('/incidents')}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-medium transition-colors shadow-xs cursor-pointer"
          >
            <span>View All Incidents</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
          </button>
        </div>
      </div>

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Active Incidents"
          value={activeCount}
          subtitle="Open or under triage"
          icon={AlertTriangle}
          trend={incidents.length > 0 ? { value: `${activeCount} open`, isPositive: activeCount === 0, label: 'Unresolved' } : { value: '0 Open', isPositive: true, label: 'Nominal' }}
        />
        <KpiCard
          title="Critical Incidents"
          value={criticalCount}
          subtitle="Highest severity tier"
          icon={Flame}
          trend={incidents.length > 0 ? { value: `${criticalCount} critical`, isPositive: criticalCount === 0, label: 'Severity P1' } : { value: '0 Critical', isPositive: true, label: 'Nominal' }}
        />
        <KpiCard
          title="Detected Anomalies"
          value={anomaliesCount}
          subtitle="Isolation Forest outliers"
          icon={Activity}
          trend={incidents.length > 0 ? { value: `${anomaliesCount} outliers`, isPositive: anomaliesCount === 0, label: 'ML Signal' } : { value: '0 Outliers', isPositive: true, label: 'Baseline' }}
        />
        <KpiCard
          title="Average Risk Score"
          value={`${avgRisk}/100`}
          subtitle="Fuzzy logic inference"
          icon={Gauge}
          trend={incidents.length > 0 ? { value: `${avgRisk}/100`, isPositive: avgRisk < 50, label: 'Composite' } : { value: '0/100', isPositive: true, label: 'Mamdani FIS' }}
        />
      </div>

      {/* Charts Section: Incident Trend & Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart (Spans 2 cols on lg) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Incident Volume & Anomaly Trend
              </h3>
            </div>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
              24-Hour Rolling
            </span>
          </div>

          <div className="h-64 w-full">
            {chartData.trends.length === 0 ? (
              <div className="h-full w-full flex flex-col items-center justify-center text-xs text-slate-400 dark:text-slate-500 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg p-4 text-center">
                <span>No incident telemetry recorded yet.</span>
                <span className="text-slate-400 dark:text-slate-500 mt-1">Incident volume and ML anomaly series will appear here as incidents are logged.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData.trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={isDark ? '#3b82f6' : '#2563eb'} stopOpacity={isDark ? 0.2 : 0.12} />
                      <stop offset="95%" stopColor={isDark ? '#3b82f6' : '#2563eb'} stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#1e293b' : '#f1f5f9'} />
                  <XAxis dataKey="time" stroke={isDark ? '#64748b' : '#94a3b8'} fontSize={11} />
                  <YAxis stroke={isDark ? '#64748b' : '#94a3b8'} fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: isDark ? '#0f172a' : '#ffffff',
                      borderColor: isDark ? '#334155' : '#e2e8f0',
                      color: isDark ? '#f8fafc' : '#0f172a',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="total"
                    name="Incidents"
                    stroke={isDark ? '#38bdf8' : '#2563eb'}
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorTotal)"
                  />
                  <Area
                    type="monotone"
                    dataKey="anomalies"
                    name="ML Anomalies"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    strokeDasharray="4 2"
                    fill="none"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Severity & Risk Distribution */}
        <div className="space-y-6">
          {/* Severity Distribution */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-3">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Severity Distribution
              </h3>
              <span className="text-xs text-slate-400 dark:text-slate-500">By Tier</span>
            </div>
            <div className="h-28 w-full">
              {incidents.length === 0 ? (
                <div className="h-full w-full flex items-center justify-center text-xs text-slate-400 dark:text-slate-500 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
                  No incidents logged
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.severityDistribution} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="2 2" stroke={isDark ? '#1e293b' : '#f1f5f9'} />
                    <XAxis dataKey="name" stroke={isDark ? '#64748b' : '#94a3b8'} fontSize={10} />
                    <YAxis stroke={isDark ? '#64748b' : '#94a3b8'} fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0f172a' : '#ffffff',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        color: isDark ? '#f8fafc' : '#0f172a',
                        borderRadius: '6px',
                        fontSize: '11px',
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {chartData.severityDistribution.map((entry, index) => (
                        <Cell key={`sev-cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-3">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Fuzzy Risk Distribution
              </h3>
              <span className="text-xs text-slate-400 dark:text-slate-500">Score Bands</span>
            </div>
            <div className="h-28 w-full">
              {incidents.length === 0 ? (
                <div className="h-full w-full flex items-center justify-center text-xs text-slate-400 dark:text-slate-500 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
                  No risk evaluations recorded
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.riskDistribution} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="2 2" stroke={isDark ? '#1e293b' : '#f1f5f9'} />
                    <XAxis dataKey="name" stroke={isDark ? '#64748b' : '#94a3b8'} fontSize={10} />
                    <YAxis stroke={isDark ? '#64748b' : '#94a3b8'} fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0f172a' : '#ffffff',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        color: isDark ? '#f8fafc' : '#0f172a',
                        borderRadius: '6px',
                        fontSize: '11px',
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {chartData.riskDistribution.map((entry, index) => (
                        <Cell key={`risk-cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xs overflow-hidden">
        <div className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Recent Incidents
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Most recent operational alerts and diagnostic findings</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/incidents')}
            className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 self-start sm:self-auto flex items-center gap-1 cursor-pointer"
          >
            <span>View All Incidents</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400 font-sans">Loading incidents...</div>
          ) : incidents.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500 dark:text-slate-400 font-sans">
              No incidents available. Ingest telemetry or create an incident to begin real-time analysis.
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/70 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Incident ID</th>
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Risk</th>
                  <th className="py-3 px-4">Anomaly</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {incidents.slice(0, 5).map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => navigate(`/incidents/${inc.id}`)}
                    className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-mono font-semibold text-blue-600 dark:text-blue-400 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                      {inc.id}
                    </td>
                    <td className="py-3 px-4 text-slate-500 dark:text-slate-400">
                      {inc.timestamp.substring(11, 16)} UTC
                    </td>
                    <td className="py-3 px-4 text-slate-800 dark:text-slate-200 font-medium">{inc.service}</td>
                    <td className="py-3 px-4">
                      <SeverityBadge severity={inc.severity} size="sm" />
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge risk={inc.risk} score={inc.riskScore} showScore />
                    </td>
                    <td className="py-3 px-4">
                      {inc.anomalyDetected ? (
                        <span className="inline-flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400 font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                          Anomaly ({(inc.anomalyScore).toFixed(2)})
                        </span>
                      ) : (
                        <span className="text-slate-500 dark:text-slate-400">Normal</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-xs text-slate-500 dark:text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 font-medium inline-flex items-center gap-1">
                        Investigate <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Service Health Overview */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Monitored Service Topologies
            </h3>
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
            {servicesList.length} Reporting Services
          </span>
        </div>

        <div className="overflow-x-auto">
          {servicesList.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 dark:text-slate-400">
              No active incidents impacting microservice health.
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/70 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-2.5 px-4">Service</th>
                  <th className="py-2.5 px-4">Health State</th>
                  <th className="py-2.5 px-4">Active Incidents</th>
                  <th className="py-2.5 px-4">Highest Severity</th>
                  <th className="py-2.5 px-4 text-right">Last Alert</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {servicesList.map((srv) => (
                  <tr key={srv.service} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-100">{srv.service}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900/60">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        {srv.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-700 dark:text-slate-300 font-semibold">{srv.incidentsCount}</td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{srv.maxSeverity}</span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-500 dark:text-slate-400">{srv.lastSeen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
