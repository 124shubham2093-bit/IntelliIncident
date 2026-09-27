import React, { useEffect, useState } from 'react';
import {
  BrainCircuit,
  Radio,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { getMLAnalyticsData, AnomalyDistributionBin } from '@/api/analytics';
import { MLMetrics, FeatureImportance, ConfusionMatrixRow } from '@/types';

export const MLAnalyticsPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MLMetrics | null>(null);
  const [featureImportance, setFeatureImportance] = useState<FeatureImportance[]>([]);
  const [confusionMatrix, setConfusionMatrix] = useState<ConfusionMatrixRow[]>([]);
  const [anomalyDistribution, setAnomalyDistribution] = useState<AnomalyDistributionBin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const res = await getMLAnalyticsData();
      setMetrics(res.data.metrics);
      setFeatureImportance(res.data.featureImportance);
      setConfusionMatrix(res.data.confusionMatrix);
      setAnomalyDistribution(res.data.anomalyDistribution);
      setLoading(false);
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
            Machine Learning Analytics
          </h1>
        </div>

        <div className="flex items-center gap-2 px-3 py-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-400">
          <span>Model Pipeline:</span>
          <code className="text-teal-400">scikit-learn &bull; Active</code>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center font-mono text-xs text-slate-400">
          Loading ML inference statistics and confusion matrices...
        </div>
      ) : (
        <>
          {/* SECTION 1: Anomaly Detection (Isolation Forest) */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                  Section 1: Anomaly Detection Engine
                </h3>
              </div>
              <span className="text-xs font-mono text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/30">
                Model: Isolation Forest (scikit-learn)
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Model info & parameters */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 space-y-3">
                <span className="text-xs font-mono font-semibold text-slate-200 block">
                  Isolation Forest Specification
                </span>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-slate-900">
                    <span className="text-slate-400">Algorithm:</span>
                    <span className="text-slate-200">Isolation Forest</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-900">
                    <span className="text-slate-400">n_estimators:</span>
                    <span className="text-slate-200">200 trees</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-900">
                    <span className="text-slate-400">Contamination:</span>
                    <span className="text-slate-200">0.05 (5%)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-900">
                    <span className="text-slate-400">Detection Status:</span>
                    <span className="text-teal-400 font-bold">Operational</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Scoring Function:</span>
                    <span className="text-slate-200">Mean Path Length</span>
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                    Input Features:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      'error_rate_5m',
                      'latency_p99_ratio',
                      'req_volume_delta',
                      'db_pool_utilization',
                      'pod_restart_count',
                      'cpu_saturation',
                    ].map((f) => (
                      <span
                        key={f}
                        className="text-[10px] font-mono bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Anomaly Distribution Chart */}
              <div className="lg:col-span-2 bg-slate-950/80 border border-slate-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Anomaly Score Distribution across Evaluation Baseline
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">N=24,500 Samples</span>
                </div>

                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={anomalyDistribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                      <XAxis dataKey="bin" stroke="#64748b" fontSize={10} fontFamily="monospace" />
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
                      <Bar dataKey="normalCount" name="Nominal Inliers" fill="#14b8a6" stackId="a" />
                      <Bar dataKey="anomalyCount" name="Anomalous Outliers" fill="#ef4444" stackId="a" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Threshold boundary: score &lt; -0.2 denotes anomalous deviation</span>
                  <span className="text-teal-400">Isolation Forest Active</span>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 2: Severity Classification (Random Forest) */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                  Section 2: Severity Multi-Class Classification
                </h3>
              </div>
              <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/30">
                Model: Random Forest Classifier
              </span>
            </div>

            {/* Performance Metrics KPI Row */}
            {metrics && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-950/80 border border-slate-800 rounded p-3">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    Accuracy
                  </span>
                  <span className="text-xl font-bold font-mono text-teal-400 mt-1 block">
                    {(metrics.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-slate-950/80 border border-slate-800 rounded p-3">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    Precision
                  </span>
                  <span className="text-xl font-bold font-mono text-teal-400 mt-1 block">
                    {(metrics.precision * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-slate-950/80 border border-slate-800 rounded p-3">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    Recall
                  </span>
                  <span className="text-xl font-bold font-mono text-teal-400 mt-1 block">
                    {(metrics.recall * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-slate-950/80 border border-slate-800 rounded p-3">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    F1 Score
                  </span>
                  <span className="text-xl font-bold font-mono text-teal-400 mt-1 block">
                    {(metrics.f1Score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Feature Importance Horizontal Bar Chart */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Gini Feature Importance
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">Relative Weight</span>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={featureImportance}
                      layout="vertical"
                      margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                      <XAxis type="number" domain={[0, 0.4]} stroke="#64748b" fontSize={10} fontFamily="monospace" />
                      <YAxis
                        dataKey="feature"
                        type="category"
                        stroke="#94a3b8"
                        fontSize={10}
                        fontFamily="monospace"
                        width={150}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          border: '1px solid #334155',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                        }}
                      />
                      <Bar dataKey="importance" fill="#8b5cf6" radius={[0, 3, 3, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Confusion Matrix Visualization */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono font-semibold text-slate-200">
                    Multi-Class Confusion Matrix (Validation Set)
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">Class Matrix</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-center border-collapse text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-800 text-[10px] text-slate-400">
                        <th className="py-2 text-left">Actual \ Predicted</th>
                        <th className="py-2 text-blue-400">Low</th>
                        <th className="py-2 text-amber-400">Medium</th>
                        <th className="py-2 text-orange-400">High</th>
                        <th className="py-2 text-rose-400">Critical</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80">
                      {confusionMatrix.map((row) => (
                        <tr key={row.actual} className="hover:bg-slate-900/50">
                          <td className="py-2.5 text-left font-bold text-slate-300">
                            {row.actual}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'LOW'
                                ? 'bg-blue-500/20 text-blue-300 font-bold'
                                : 'text-slate-400'
                            }`}
                          >
                            {row.low}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'MEDIUM'
                                ? 'bg-amber-500/20 text-amber-300 font-bold'
                                : 'text-slate-400'
                            }`}
                          >
                            {row.medium}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'HIGH'
                                ? 'bg-orange-500/20 text-orange-300 font-bold'
                                : 'text-slate-400'
                            }`}
                          >
                            {row.high}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-300 font-bold'
                                : 'text-slate-400'
                            }`}
                          >
                            {row.critical}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 p-2.5 rounded bg-slate-900/60 border border-slate-800/80 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                  <span>Class weights balanced via stratified cross-validation</span>
                  <span className="text-teal-400">Random Forest Classifier</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
