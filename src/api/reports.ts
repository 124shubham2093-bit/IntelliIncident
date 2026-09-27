import { apiClient } from './client';
import { IncidentDetails, RootCauseCandidate } from '@/types';

export interface IncidentReportResponse {
  incident: IncidentDetails;
  generatedAt: string;
  reportId: string;
  summaryTitle: string;
}

/**
 * Fetch formal incident post-mortem report data by incident ID.
 */
export async function getIncidentReport(
  incidentId: string
): Promise<{ data: IncidentReportResponse | null; isDemo: boolean }> {
  try {
    const report = await apiClient<IncidentReportResponse>(`/api/reports/${incidentId}`);
    return { data: report, isDemo: false };
  } catch (err) {
    console.warn(`Report fetch failed for ${incidentId}:`, err);
    return { data: null, isDemo: false };
  }
}

/**
 * Fetch evidence-based root cause rankings for an incident.
 */
export async function getRootCauseAnalysis(
  incidentId: string
): Promise<{ data: RootCauseCandidate[]; isDemo: boolean }> {
  try {
    const candidates = await apiClient<RootCauseCandidate[]>(`/api/root-cause/${incidentId}`);
    return { data: candidates || [], isDemo: false };
  } catch (err) {
    console.warn(`RCA fetch failed for ${incidentId}:`, err);
    return { data: [], isDemo: false };
  }
}

