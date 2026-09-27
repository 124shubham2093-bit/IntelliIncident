import { apiClient } from './client';
import { ConfusionMatrixRow, FeatureImportance, MLMetrics, Incident } from '@/types';

export interface AnomalyDistributionBin {
  bin: string;
  normalCount: number;
  anomalyCount: number;
  scoreRange: string;
}

export interface MLAnalyticsResponse {
  metrics: MLMetrics | null;
  featureImportance: FeatureImportance[];
  confusionMatrix: ConfusionMatrixRow[];
  anomalyDistribution: AnomalyDistributionBin[];
}

/**
 * Fetch trained ML model performance metrics.
 */
export async function getMLMetrics(): Promise<{ data: MLMetrics | null; isDemo: boolean }> {
  try {
    const data = await apiClient<MLMetrics>('/api/ml/metrics');
    return { data, isDemo: false };
  } catch (err) {
    console.warn('Failed to fetch ML metrics from /api/ml/metrics:', err);
    return { data: null, isDemo: false };
  }
}

/**
 * Fetch feature importances for Random Forest severity classifier.
 */
export async function getMLFeatures(): Promise<{ data: FeatureImportance[]; isDemo: boolean }> {
  try {
    const data = await apiClient<FeatureImportance[]>('/api/ml/features');
    return { data: data || [], isDemo: false };
  } catch (err) {
    console.warn('Failed to fetch ML features from /api/ml/features:', err);
    return { data: [], isDemo: false };
  }
}

/**
 * Fetch comprehensive ML analytics payload from genuine trained model metadata.
 */
export async function getMLAnalyticsData(): Promise<{ data: MLAnalyticsResponse; isDemo: boolean }> {
  try {
    const [metrics, features, confusionMatrix, anomalyDistribution] = await Promise.all([
      apiClient<MLMetrics>('/api/ml/metrics').catch(() => null),
      apiClient<FeatureImportance[]>('/api/ml/features').catch(() => []),
      apiClient<ConfusionMatrixRow[]>('/api/ml/confusion-matrix').catch(() => []),
      apiClient<AnomalyDistributionBin[]>('/api/ml/anomaly-distribution').catch(() => []),
    ]);

    return {
      data: {
        metrics,
        featureImportance: features || [],
        confusionMatrix: confusionMatrix || [],
        anomalyDistribution: anomalyDistribution || [],
      },
      isDemo: false,
    };
  } catch (err) {
    console.warn('Failed to fetch ML analytics data:', err);
    return {
      data: {
        metrics: null,
        featureImportance: [],
        confusionMatrix: [],
        anomalyDistribution: [],
      },
      isDemo: false,
    };
  }
}

/**
 * Dynamically computes dashboard chart distributions from the genuine incidents dataset.
 */
export function getDashboardChartData(incidents: Incident[] = []) {
  const severityDistribution = [
    { name: 'Low', count: incidents.filter((i) => i.severity === 'LOW').length, color: '#3b82f6' },
    { name: 'Medium', count: incidents.filter((i) => i.severity === 'MEDIUM').length, color: '#eab308' },
    { name: 'High', count: incidents.filter((i) => i.severity === 'HIGH').length, color: '#f97316' },
    { name: 'Critical', count: incidents.filter((i) => i.severity === 'CRITICAL').length, color: '#ef4444' },
  ];

  const riskDistribution = [
    { name: 'Low', count: incidents.filter((i) => i.risk === 'LOW').length, color: '#3b82f6' },
    { name: 'Medium', count: incidents.filter((i) => i.risk === 'MEDIUM').length, color: '#eab308' },
    { name: 'High', count: incidents.filter((i) => i.risk === 'HIGH').length, color: '#f97316' },
    { name: 'Critical', count: incidents.filter((i) => i.risk === 'CRITICAL' || i.risk === 'VERY_HIGH').length, color: '#ef4444' },
  ];

  // Derive 24h rolling trend buckets from real incidents
  const trends: { time: string; total: number; anomalies: number }[] = [];
  if (incidents.length > 0) {
    // Generate buckets based on unique incident timestamp hours or simple distribution
    const hourBuckets: Record<string, { total: number; anomalies: number }> = {};
    for (const inc of incidents) {
      const timeLabel = inc.timestamp ? inc.timestamp.substring(11, 16) : 'Now';
      if (!hourBuckets[timeLabel]) {
        hourBuckets[timeLabel] = { total: 0, anomalies: 0 };
      }
      hourBuckets[timeLabel].total += 1;
      if (inc.anomalyDetected) {
        hourBuckets[timeLabel].anomalies += 1;
      }
    }
    for (const [time, counts] of Object.entries(hourBuckets)) {
      trends.push({ time, total: counts.total, anomalies: counts.anomalies });
    }
  }

  return {
    trends,
    severityDistribution,
    riskDistribution,
  };
}

