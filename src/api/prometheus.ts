import { apiClient } from './client';
import {
  PrometheusStatus,
  PrometheusMetricSample,
  PrometheusEvidence,
} from '@/types';

/**
 * Fetch Prometheus reachability and server status.
 * Safe endpoint: never throws and returns normalized status.
 */
export async function getPrometheusHealth(): Promise<{ data: PrometheusStatus | null }> {
  try {
    const status = await apiClient<PrometheusStatus>('/api/prometheus/health');
    return { data: status };
  } catch (err) {
    console.warn('Failed to fetch Prometheus health status:', err);
    return {
      data: {
        status: 'UNAVAILABLE',
        url: '',
        reachable: false,
        message: 'Prometheus service unreachable from client.',
      },
    };
  }
}

/**
 * Fetch instant metric samples for a target service from Prometheus.
 */
export async function getPrometheusMetrics(
  service?: string
): Promise<{ data: Record<string, PrometheusMetricSample> | null }> {
  try {
    const params = new URLSearchParams();
    if (service) params.set('service', service);
    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const metrics = await apiClient<Record<string, PrometheusMetricSample>>(
      `/api/prometheus/metrics${queryStr}`
    );
    return { data: metrics || {} };
  } catch (err) {
    console.warn('Failed to fetch Prometheus metrics:', err);
    return { data: null };
  }
}

/**
 * Fetch Prometheus metric evidence correlated for a specific incident.
 */
export async function getPrometheusEvidence(
  incidentId: string
): Promise<{ data: PrometheusEvidence | null }> {
  try {
    const evidence = await apiClient<PrometheusEvidence>(
      `/api/prometheus/evidence/${encodeURIComponent(incidentId)}`
    );
    return { data: evidence };
  } catch (err) {
    console.warn(`Failed to fetch Prometheus evidence for incident ${incidentId}:`, err);
    return { data: null };
  }
}
