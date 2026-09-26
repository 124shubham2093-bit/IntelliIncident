import { apiClient } from './client';
import { IncidentDetails, RootCauseCandidate } from '@/types';
import { getDemoIncidentDetails } from '@/data/demoIncidents';

export interface IncidentReportResponse {
  incident: IncidentDetails;
  generatedAt: string;
  reportId: string;
  summaryTitle: string;
}

/**
 * Fetch formal incident post-mortem report data by incident ID.
 * Future endpoint: GET /api/reports/{id}
 */
export async function getIncidentReport(
  incidentId: string
): Promise<{ data: IncidentReportResponse; isDemo: boolean }> {
  try {
    const report = await apiClient<IncidentReportResponse>(`/api/reports/${incidentId}`);
    return { data: report, isDemo: false };
  } catch {
    const incident = getDemoIncidentDetails(incidentId);
    return {
      data: {
        incident,
        generatedAt: new Date().toISOString(),
        reportId: `REP-${incidentId}-${Math.floor(Date.now() / 1000)}`,
        summaryTitle: `Root Cause Analysis & Incident Post-Mortem: ${incident.title}`,
      },
      isDemo: true,
    };
  }
}

/**
 * Fetch evidence-based root cause rankings for an incident.
 * Future endpoint: GET /api/root-cause/{id}
 */
export async function getRootCauseAnalysis(
  incidentId: string
): Promise<{ data: RootCauseCandidate[]; isDemo: boolean }> {
  try {
    const candidates = await apiClient<RootCauseCandidate[]>(`/api/root-cause/${incidentId}`);
    return { data: candidates, isDemo: false };
  } catch {
    const incident = getDemoIncidentDetails(incidentId);
    return { data: incident.rootCauseCandidates, isDemo: true };
  }
}
