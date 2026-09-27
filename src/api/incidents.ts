import { apiClient } from './client';
import { Incident, IncidentDetails, IncidentAnalysis } from '@/types';

export interface IncidentFilters {
  search?: string;
  severity?: string;
  risk?: string;
  service?: string;
  status?: string;
}

/**
 * Fetch all incidents with optional filtering directly from the backend API.
 * Returns empty array when database contains no incidents.
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
    return { data: incidents || [], isDemo: false };
  } catch (err) {
    console.warn('Backend /api/incidents unavailable or returned error:', err);
    return { data: [], isDemo: false };
  }
}

/**
 * Fetch single incident detailed record by ID directly from the backend API.
 */
export async function getIncidentById(id: string): Promise<{ data: IncidentDetails | null; isDemo: boolean }> {
  try {
    const incident = await apiClient<IncidentDetails>(`/api/incidents/${id}`);
    return { data: incident, isDemo: false };
  } catch (err) {
    console.warn(`Failed to fetch incident ${id}:`, err);
    return { data: null, isDemo: false };
  }
}

/**
 * Ingest a new operational incident and run the live intelligence pipeline.
 */
export async function createIncident(payload: any): Promise<IncidentDetails> {
  return await apiClient<IncidentDetails>('/api/incidents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Trigger backend ML analysis on an incident.
 */
export async function analyzeIncident(id: string): Promise<{ data: IncidentAnalysis | null; isDemo: boolean }> {
  try {
    const analysis = await apiClient<IncidentAnalysis>(`/api/analyze/${id}`, {
      method: 'POST',
    });
    return { data: analysis, isDemo: false };
  } catch (err) {
    console.warn(`Analysis failed for incident ${id}:`, err);
    return { data: null, isDemo: false };
  }
}

