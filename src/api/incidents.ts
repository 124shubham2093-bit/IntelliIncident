import { apiClient } from './client';
import { Incident, IncidentDetails, IncidentAnalysis } from '@/types';
import { DEMO_INCIDENTS_SUMMARY, getDemoIncidentDetails } from '@/data/demoIncidents';

export interface IncidentFilters {
  search?: string;
  severity?: string;
  risk?: string;
  service?: string;
  status?: string;
}

/**
 * Fetch all incidents with optional filtering.
 * Falls back to demo dataset if API is unreachable.
 */
export async function getIncidents(filters?: IncidentFilters): Promise<{ data: Incident[]; isDemo: boolean }> {
  try {
    const params = new URLSearchParams();
    if (filters?.search) params.set('search', filters.search);
    if (filters?.severity) params.set('severity', filters.severity);
    if (filters?.risk) params.set('risk', filters.risk);
    if (filters?.service) params.set('service', filters.service);
    if (filters?.status) params.set('status', filters.status);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const incidents = await apiClient<Incident[]>(`/api/incidents${queryString}`);
    return { data: incidents, isDemo: false };
  } catch {
    // API disconnected: filter demo data locally
    let list = [...DEMO_INCIDENTS_SUMMARY];

    if (filters?.search) {
      const q = filters.search.toLowerCase();
      list = list.filter(
        (i) => i.id.toLowerCase().includes(q) || i.title.toLowerCase().includes(q) || i.service.toLowerCase().includes(q)
      );
    }
    if (filters?.severity && filters.severity !== 'ALL') {
      list = list.filter((i) => i.severity === filters.severity);
    }
    if (filters?.risk && filters.risk !== 'ALL') {
      list = list.filter((i) => i.risk === filters.risk);
    }
    if (filters?.service && filters.service !== 'ALL') {
      list = list.filter((i) => i.service === filters.service);
    }
    if (filters?.status && filters.status !== 'ALL') {
      list = list.filter((i) => i.status === filters.status);
    }

    return { data: list, isDemo: true };
  }
}

/**
 * Fetch single incident detailed record by ID.
 * Falls back to demo detailed data if API is unreachable.
 */
export async function getIncidentById(id: string): Promise<{ data: IncidentDetails; isDemo: boolean }> {
  try {
    const incident = await apiClient<IncidentDetails>(`/api/incidents/${id}`);
    return { data: incident, isDemo: false };
  } catch {
    const fallback = getDemoIncidentDetails(id);
    return { data: fallback, isDemo: true };
  }
}

/**
 * Trigger backend ML analysis on an incident.
 * Future endpoint: POST /api/analyze/{id}
 */
export async function analyzeIncident(id: string): Promise<{ data: IncidentAnalysis; isDemo: boolean }> {
  try {
    const analysis = await apiClient<IncidentAnalysis>(`/api/analyze/${id}`, {
      method: 'POST',
    });
    return { data: analysis, isDemo: false };
  } catch {
    const detail = getDemoIncidentDetails(id);
    const demoAnalysis: IncidentAnalysis = {
      incidentId: id,
      analyzedAt: new Date().toISOString(),
      anomaly: detail.mlAnalysis.anomaly,
      severityPrediction: detail.mlAnalysis.severityPrediction,
      fuzzyRisk: detail.fuzzyRisk,
      rootCauses: detail.rootCauseCandidates,
      recommendations: detail.recommendations,
    };
    return { data: demoAnalysis, isDemo: true };
  }
}
