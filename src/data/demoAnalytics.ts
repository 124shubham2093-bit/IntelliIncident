import { ConfusionMatrixRow, FeatureImportance, MLMetrics } from '@/types';

export const DEMO_ML_METRICS: MLMetrics = {
  accuracy: 0.942,
  precision: 0.928,
  recall: 0.915,
  f1Score: 0.921,
  trainingSamplesCount: 24500,
  lastTrainedDate: '2026-09-24T02:00:00Z',
};

export const DEMO_FEATURE_IMPORTANCE: FeatureImportance[] = [
  { feature: 'Error Rate Spike (5m Delta)', importance: 0.32, category: 'Error Telemetry' },
  { feature: 'P99 Latency Ratio to Baseline', importance: 0.24, category: 'Latency' },
  { feature: 'Deployment Recency (< 60m)', importance: 0.18, category: 'Change Events' },
  { feature: 'Active User Impact Volume', importance: 0.12, category: 'Business SLA' },
  { feature: 'Database Connection Pool %', importance: 0.08, category: 'Infrastructure' },
  { feature: 'CPU Saturation (> 85%)', importance: 0.06, category: 'Infrastructure' },
];

export const DEMO_CONFUSION_MATRIX: ConfusionMatrixRow[] = [
  { actual: 'LOW', low: 480, medium: 24, high: 5, critical: 1 },
  { actual: 'MEDIUM', low: 18, medium: 410, high: 22, critical: 4 },
  { actual: 'HIGH', low: 4, medium: 28, high: 360, high_or_crit: 16, critical: 16 } as unknown as ConfusionMatrixRow,
  { actual: 'CRITICAL', low: 0, medium: 3, high: 14, critical: 240 },
];

export const DEMO_ANOMALY_DISTRIBUTION = [
  { bin: '-0.8 to -0.6', normalCount: 0, anomalyCount: 42, scoreRange: 'Severe Anomaly' },
  { bin: '-0.6 to -0.4', normalCount: 0, anomalyCount: 110, scoreRange: 'High Anomaly' },
  { bin: '-0.4 to -0.2', normalCount: 15, anomalyCount: 65, scoreRange: 'Borderline' },
  { bin: '-0.2 to 0.0', normalCount: 180, anomalyCount: 12, scoreRange: 'Mild Inlier' },
  { bin: '0.0 to 0.2', normalCount: 650, anomalyCount: 0, scoreRange: 'Normal' },
  { bin: '0.2 to 0.4', normalCount: 1420, anomalyCount: 0, scoreRange: 'Normal' },
  { bin: '0.4 to 0.6', normalCount: 980, anomalyCount: 0, scoreRange: 'Nominal Baseline' },
];

export const DEMO_INCIDENT_TRENDS = [
  { time: '00:00', total: 2, critical: 0, anomalies: 3 },
  { time: '03:00', total: 1, critical: 0, anomalies: 1 },
  { time: '06:00', total: 3, critical: 0, anomalies: 4 },
  { time: '09:00', total: 6, critical: 1, anomalies: 8 },
  { time: '12:00', total: 8, critical: 2, anomalies: 12 },
  { time: '15:00', total: 5, critical: 1, anomalies: 7 },
  { time: '18:00', total: 4, critical: 0, anomalies: 5 },
  { time: '21:00', total: 3, critical: 0, anomalies: 4 },
];

export const DEMO_SEVERITY_DISTRIBUTION = [
  { name: 'Low', count: 18, color: '#3b82f6' },
  { name: 'Medium', count: 12, color: '#eab308' },
  { name: 'High', count: 8, color: '#f97316' },
  { name: 'Critical', count: 3, color: '#ef4444' },
];

export const DEMO_RISK_DISTRIBUTION = [
  { name: 'Low', count: 15, color: '#3b82f6' },
  { name: 'Medium', count: 14, color: '#eab308' },
  { name: 'High', count: 9, color: '#f97316' },
  { name: 'Critical', count: 3, color: '#ef4444' },
];
