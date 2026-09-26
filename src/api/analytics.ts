import { apiClient } from './client';
import { FeatureImportance, MLMetrics } from '@/types';
import {
  DEMO_CONFUSION_MATRIX,
  DEMO_FEATURE_IMPORTANCE,
  DEMO_ML_METRICS,
  DEMO_ANOMALY_DISTRIBUTION,
  DEMO_INCIDENT_TRENDS,
  DEMO_SEVERITY_DISTRIBUTION,
  DEMO_RISK_DISTRIBUTION,
} from '@/data/demoAnalytics';

export interface MLAnalyticsResponse {
  metrics: MLMetrics;
  featureImportance: FeatureImportance[];
  confusionMatrix: typeof DEMO_CONFUSION_MATRIX;
  anomalyDistribution: typeof DEMO_ANOMALY_DISTRIBUTION;
}

/**
 * Fetch trained ML model performance metrics.
 * Falls back to demo metrics when backend is disconnected.
 */
export async function getMLMetrics(): Promise<{ data: MLMetrics; isDemo: boolean }> {
  try {
    const data = await apiClient<MLMetrics>('/api/ml/metrics');
    return { data, isDemo: false };
  } catch {
    return { data: DEMO_ML_METRICS, isDemo: true };
  }
}

/**
 * Fetch feature importances for Random Forest severity classifier.
 */
export async function getMLFeatures(): Promise<{ data: FeatureImportance[]; isDemo: boolean }> {
  try {
    const data = await apiClient<FeatureImportance[]>('/api/ml/features');
    return { data, isDemo: false };
  } catch {
    return { data: DEMO_FEATURE_IMPORTANCE, isDemo: true };
  }
}

/**
 * Fetch comprehensive ML analytics payload.
 */
export async function getMLAnalyticsData(): Promise<{ data: MLAnalyticsResponse; isDemo: boolean }> {
  try {
    const metrics = await apiClient<MLMetrics>('/api/ml/metrics');
    const features = await apiClient<FeatureImportance[]>('/api/ml/features');
    return {
      data: {
        metrics,
        featureImportance: features,
        confusionMatrix: DEMO_CONFUSION_MATRIX,
        anomalyDistribution: DEMO_ANOMALY_DISTRIBUTION,
      },
      isDemo: false,
    };
  } catch {
    return {
      data: {
        metrics: DEMO_ML_METRICS,
        featureImportance: DEMO_FEATURE_IMPORTANCE,
        confusionMatrix: DEMO_CONFUSION_MATRIX,
        anomalyDistribution: DEMO_ANOMALY_DISTRIBUTION,
      },
      isDemo: true,
    };
  }
}

export function getDashboardChartData() {
  return {
    trends: DEMO_INCIDENT_TRENDS,
    severityDistribution: DEMO_SEVERITY_DISTRIBUTION,
    riskDistribution: DEMO_RISK_DISTRIBUTION,
  };
}
