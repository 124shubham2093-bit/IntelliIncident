import { apiClient, API_BASE_URL } from './client';
import { SystemStatus } from '@/types';

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  service: string;
  version?: string;
  mlEngineReady?: boolean;
  fuzzyEngineReady?: boolean;
}

/**
 * Checks system health against future FastAPI backend.
 * Falls back to disconnected state if backend is unreachable.
 */
export async function getSystemHealth(): Promise<SystemStatus> {
  const defaultDisconnected: SystemStatus = {
    frontendStatus: 'READY',
    apiStatus: 'DISCONNECTED',
    mlModelsStatus: 'PENDING',
    fuzzyEngineStatus: 'PENDING',
    backendUrl: API_BASE_URL,
    lastChecked: new Date().toISOString(),
  };

  try {
    const data = await apiClient<HealthResponse>('/api/health', { timeoutMs: 2000 });
    return {
      frontendStatus: 'READY',
      apiStatus: data.status === 'ok' ? 'CONNECTED' : 'DISCONNECTED',
      mlModelsStatus: data.mlEngineReady ? 'READY' : 'PENDING',
      fuzzyEngineStatus: data.fuzzyEngineReady ? 'READY' : 'PENDING',
      backendUrl: API_BASE_URL,
      lastChecked: new Date().toISOString(),
    };
  } catch {
    // Expected when FastAPI is not running
    return defaultDisconnected;
  }
}
