import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Flame,
  Radio,
  Gauge,
  TrendingUp,
  Server,
  Cpu,
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
import { KpiCard } from '@/components/Common/KpiCard';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { getIncidents } from '@/api/incidents';
import { getDashboardChartData } from '@/api/analytics';
import { DEMO_SERVICES_HEALTH } from '@/data/demoIncidents';
import { Incident } from '@/types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  const chartData = getDashboardChartData();

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await getIncidents();
      setIncidents(res.data);
      setLoading(false);
    }
    loadData();
  }, []);

  const activeCount = incidents.filter((i) => i.status !== 'RESOLVED').length;
  const criticalCount = incidents.filter((i) => i.severity === 'CRITICAL').length;
  const anomaliesCount = incidents.filter((i) => i.anomalyDetected).length;
  const avgRisk = Math.round(
    incidents.reduce((acc, curr) => acc + curr.riskScore, 0) / (incidents.length || 1)
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
            Incident Intelligence Dashboard
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate('/incidents')}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 text-xs font-mono font-medium transition-colors cursor-pointer"
          >
            <span>View All Incidents</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Active Incidents"
          value={activeCount}
          subtitle="Currently open or under triage"
          icon={AlertTriangle}
          accentColor="amber"
          trend={{ value: '+2 in 24h', isPositive: false, label: 'Unresolved' }}
        />
        <KpiCard
          title="Critical Incidents"
          value={criticalCount}
          subtitle="Tier-1 customer impact"
          icon={Flame}
          accentColor="rose"
          trend={{ value: 'Immediate Action', isPositive: false, label: 'P1 Severity' }}
        />
        <KpiCard
          title="Detected Anomalies"
          value={anomaliesCount}
          subtitle="Isolation Forest outliers"
          icon={Radio}
          accentColor="teal"
          trend={{ value: 'Contamination 0.05', isPositive: true, label: 'ML Signal' }}
        />
        <KpiCard
          title="Average Risk Score"
          value={`${avgRisk}/100`}
          subtitle="Fuzzy inference composite"
          icon={Gauge}
          accentColor="blue"
          trend={{ value: 'High Risk Cluster', isPositive: false, label: 'Soft Computing' }}
        />
      </div>

      {/* Charts Section: Incident Trend & Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart (Spans 2 cols on lg) */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-lg p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-teal-400" />
              <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Incident Trend (24h Rolling Window)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              Live Feed
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData.trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorAnomalies" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} fontFamily="monospace" />
                <YAxis stroke="#64748b" fontSize={11} fontFamily="monospace" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="total"
                  name="Incidents"
                  stroke="#14b8a6"
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
                  fillOpacity={1}
                  fill="url(#colorAnomalies)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity & Risk Distribution */}
        <div className="space-y-6">
          {/* Severity Distribution */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
              <h3 className="text-xs font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Severity Distribution
              </h3>
              <span className="text-[10px] font-mono text-slate-400">Class Split</span>
            </div>
            <div className="h-28 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData.severityDistribution} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} fontFamily="monospace" />
                  <YAxis stroke="#64748b" fontSize={10} fontFamily="monospace" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                    }}
                  />
                  <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                    {chartData.severityDistribution.map((entry, index) => (
                      <Cell key={`sev-cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
              <h3 className="text-xs font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Risk Distribution
              </h3>
              <span className="text-[10px] font-mono text-slate-400">Fuzzy Quantiles</span>
            </div>
            <div className="h-28 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData.riskDistribution} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} fontFamily="monospace" />
                  <YAxis stroke="#64748b" fontSize={10} fontFamily="monospace" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                    }}
                  />
                  <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                    {chartData.riskDistribution.map((entry, index) => (
                      <Cell key={`risk-cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono">
              Recent Incidents
            </h3>
          </div>
          <button
            type="button"
            onClick={() => navigate('/incidents')}
            className="text-xs font-mono text-teal-400 hover:text-teal-300 self-start sm:self-auto flex items-center gap-1 cursor-pointer"
          >
            <span>Full Incident Table</span>
            <ExternalLink className="w-3 h-3" />
          </button>
        </div>

        <div className="mt-4 overflow-x-auto">
          {loading ? (
            <div className="py-8 text-center text-xs font-mono text-slate-400">Loading incidents...</div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase tracking-wider bg-slate-950/40">
                  <th className="py-3 px-3">Incident ID</th>
                  <th className="py-3 px-3">Time</th>
                  <th className="py-3 px-3">Service</th>
                  <th className="py-3 px-3">Severity</th>
                  <th className="py-3 px-3">Risk</th>
                  <th className="py-3 px-3">Anomaly</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {incidents.slice(0, 5).map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => navigate(`/incidents/${inc.id}`)}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-3 font-semibold text-teal-400 group-hover:underline">
                      {inc.id}
                    </td>
                    <td className="py-3 px-3 text-slate-400 text-[11px]">
                      {inc.timestamp.substring(11, 16)} UTC
                    </td>
                    <td className="py-3 px-3 text-slate-200 font-sans">{inc.service}</td>
                    <td className="py-3 px-3">
                      <SeverityBadge severity={inc.severity} size="sm" />
                    </td>
                    <td className="py-3 px-3">
                      <RiskBadge risk={inc.risk} score={inc.riskScore} showScore />
                    </td>
                    <td className="py-3 px-3">
                      {inc.anomalyDetected ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-rose-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
                          Anomaly ({(inc.anomalyScore).toFixed(2)})
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400">Normal</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-[11px] text-slate-400 group-hover:text-teal-300 font-medium inline-flex items-center gap-1">
                        Investigate <ArrowRight className="w-3 h-3" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Dual Section: Service Health & ML Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Health Section */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-slate-400" />
              <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Service Health
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
              {DEMO_SERVICES_HEALTH.length} Services Monitored
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase">
                  <th className="py-2.5 px-2">Service</th>
                  <th className="py-2.5 px-2">Status</th>
                  <th className="py-2.5 px-2">Error Rate</th>
                  <th className="py-2.5 px-2">Latency</th>
                  <th className="py-2.5 px-2 text-right">Last Deployment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {DEMO_SERVICES_HEALTH.map((s) => (
                  <tr key={s.service} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-2 font-medium text-slate-200">{s.service}</td>
                    <td className="py-2.5 px-2">
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          s.status === 'HEALTHY'
                            ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30'
                            : s.status === 'DEGRADED'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-2 text-slate-300">{s.errorRate}%</td>
                    <td className="py-2.5 px-2 text-slate-300">{s.latency}ms</td>
                    <td className="py-2.5 px-2 text-right text-slate-400 text-[11px]">
                      {s.lastDeployment}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ML Status Section */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                  ML Status
                </h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/30">
                Active Models
              </span>
            </div>

            <div className="space-y-4">
              {/* Anomaly Detection Status */}
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-md">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Anomaly Detection
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/30">
                    Operational (v1.2)
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-400 font-sans">
                  Isolation Forest algorithm configured for telemetry streaming and continuous deviation scoring.
                </p>
              </div>

              {/* Severity Classification Status */}
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-md">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Severity Classification
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/30">
                    Operational (v2.0)
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-400 font-sans">
                  Random Forest multi-class model with feature extraction. Predicts Low, Medium, High, Critical severities.
                </p>
              </div>

              {/* Fuzzy Risk Engine Status */}
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-md">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Fuzzy Risk Engine
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/30">
                    Active Inference
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-400 font-sans">
                  Soft Computing Mamdani-style inference engine with continuous membership functions and heuristic operational rule sets.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Model Pipeline: Scikit-Learn & Mamdani Fuzzy System</span>
            <span className="text-teal-400">Telemetry Synced</span>
          </div>
        </div>
      </div>
    </div>
  );
};
