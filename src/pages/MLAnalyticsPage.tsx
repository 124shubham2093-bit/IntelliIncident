import React, { useEffect, useState } from 'react';
import {
  BrainCircuit,
  Activity,
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-sans">
            Machine Learning Analytics
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Statistical validation metrics, outlier distributions, and classifier performance
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-white border border-slate-200 text-xs text-slate-600 shadow-2xs">
          <span>Model Engine:</span>
          <span className="font-semibold text-blue-700">scikit-learn &bull; Active</span>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500 font-sans">
          Loading ML inference statistics and confusion matrices...
        </div>
      ) : (
        <>
          {/* SECTION 1: Anomaly Detection (Isolation Forest) */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-4 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Anomaly Detection Engine (Isolation Forest)
                </h3>
              </div>
              <span className="text-xs font-medium text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                Model: Isolation Forest
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Model info & parameters */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3">
                <span className="text-xs font-semibold text-slate-800 block">
                  Hyperparameter Specifications
                </span>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Algorithm:</span>
                    <span className="text-slate-800 font-medium">Isolation Forest</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">n_estimators:</span>
                    <span className="text-slate-800 font-medium">200 trees</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Contamination:</span>
                    <span className="text-slate-800 font-medium">0.05 (5%)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200">
                    <span className="text-slate-500">Detection Status:</span>
                    <span className="text-emerald-700 font-semibold">Operational</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Scoring Function:</span>
                    <span className="text-slate-800 font-medium">Mean Path Length</span>
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
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
                        className="text-[11px] font-mono bg-white text-slate-700 px-2 py-0.5 rounded border border-slate-200 shadow-2xs"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Anomaly Distribution Chart */}
              <div className="lg:col-span-2 bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-800">
                    Anomaly Score Distribution across Evaluation Baseline
                  </span>
                  <span className="text-xs text-slate-500 font-medium">N=24,500 Samples</span>
                </div>

                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={anomalyDistribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="2 2" stroke="#e2e8f0" />
                      <XAxis dataKey="bin" stroke="#94a3b8" fontSize={10} />
                      <YAxis stroke="#94a3b8" fontSize={10} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          border: '1px solid #e2e8f0',
                          borderRadius: '6px',
                          fontSize: '11px',
                        }}
                      />
                      <Bar dataKey="normalCount" name="Nominal Inliers" fill="#2563eb" stackId="a" />
                      <Bar dataKey="anomalyCount" name="Anomalous Outliers" fill="#ef4444" stackId="a" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                  <span>Threshold boundary: score &lt; -0.2 denotes anomalous deviation</span>
                  <span className="text-blue-700 font-medium">Isolation Forest Active</span>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 2: Severity Classification (Random Forest) */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-4 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Multi-Class Severity Classifier
                </h3>
              </div>
              <span className="text-xs font-medium text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-200">
                Model: Random Forest Classifier
              </span>
            </div>

            {/* Performance Metrics KPI Row */}
            {metrics && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5">
                  <span className="text-xs text-slate-500 font-medium block">
                    Accuracy
                  </span>
                  <span className="text-xl font-bold text-slate-900 mt-1 block">
                    {(metrics.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5">
                  <span className="text-xs text-slate-500 font-medium block">
                    Precision
                  </span>
                  <span className="text-xl font-bold text-slate-900 mt-1 block">
                    {(metrics.precision * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5">
                  <span className="text-xs text-slate-500 font-medium block">
                    Recall
                  </span>
                  <span className="text-xl font-bold text-slate-900 mt-1 block">
                    {(metrics.recall * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5">
                  <span className="text-xs text-slate-500 font-medium block">
                    F1 Score
                  </span>
                  <span className="text-xl font-bold text-slate-900 mt-1 block">
                    {(metrics.f1Score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Feature Importance Horizontal Bar Chart */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-800">
                    Gini Feature Importance
                  </span>
                  <span className="text-xs text-slate-500">Relative Weight</span>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={featureImportance}
                      layout="vertical"
                      margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="2 2" stroke="#e2e8f0" />
                      <XAxis type="number" domain={[0, 0.4]} stroke="#94a3b8" fontSize={10} />
                      <YAxis
                        dataKey="feature"
                        type="category"
                        stroke="#64748b"
                        fontSize={10}
                        width={150}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#ffffff',
                          border: '1px solid #e2e8f0',
                          borderRadius: '6px',
                          fontSize: '11px',
                        }}
                      />
                      <Bar dataKey="importance" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Confusion Matrix Visualization */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-800">
                    Multi-Class Confusion Matrix (Validation Set)
                  </span>
                  <span className="text-xs text-slate-500">Cross-Validation</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-center border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-[11px] text-slate-600 font-semibold uppercase">
                        <th className="py-2 text-left">Actual \ Predicted</th>
                        <th className="py-2 text-blue-700">Low</th>
                        <th className="py-2 text-amber-700">Medium</th>
                        <th className="py-2 text-orange-700">High</th>
                        <th className="py-2 text-red-700">Critical</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {confusionMatrix.map((row) => (
                        <tr key={row.actual} className="hover:bg-white/60">
                          <td className="py-2.5 text-left font-bold text-slate-800">
                            {row.actual}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'LOW'
                                ? 'bg-blue-100 text-blue-900 font-bold'
                                : 'text-slate-600'
                            }`}
                          >
                            {row.low}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'MEDIUM'
                                ? 'bg-amber-100 text-amber-900 font-bold'
                                : 'text-slate-600'
                            }`}
                          >
                            {row.medium}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'HIGH'
                                ? 'bg-orange-100 text-orange-900 font-bold'
                                : 'text-slate-600'
                            }`}
                          >
                            {row.high}
                          </td>
                          <td
                            className={`py-2.5 ${
                              row.actual === 'CRITICAL'
                                ? 'bg-red-100 text-red-900 font-bold'
                                : 'text-slate-600'
                            }`}
                          >
                            {row.critical}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 p-2.5 rounded-md bg-white border border-slate-200 text-xs text-slate-500 flex items-center justify-between">
                  <span>Class weights balanced via stratified cross-validation</span>
                  <span className="font-semibold text-blue-700">Random Forest Classifier</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
