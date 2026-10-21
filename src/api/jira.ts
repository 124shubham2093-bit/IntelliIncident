import { apiClient } from './client';
import {
  JiraStatus,
  JiraIssue,
  JiraEvidence,
} from '@/types';

/**
 * Fetch Jira reachability and authentication status.
 * Safe endpoint: never throws and never exposes credentials.
 */
export async function getJiraHealth(): Promise<{ data: JiraStatus | null }> {
  try {
    const status = await apiClient<JiraStatus>('/api/jira/health');
    return { data: status };
  } catch (err) {
    console.warn('Failed to fetch Jira health status:', err);
    return {
      data: {
        configured: false,
        authenticated: false,
        reachable: false,
        base_url: '',
        message: 'Jira service unreachable from client.',
      },
    };
  }
}

/**
 * Fetch Jira issues matching an optional JQL query or current project.
 */
export async function getJiraIssues(
  jql?: string,
  limit = 20
): Promise<{ data: JiraIssue[] }> {
  try {
    const params = new URLSearchParams();
    if (jql) params.set('jql', jql);
    params.set('limit', String(limit));
    const issues = await apiClient<JiraIssue[]>(`/api/jira/issues?${params.toString()}`);
    return { data: issues || [] };
  } catch (err) {
    console.warn('Failed to fetch Jira issues:', err);
    return { data: [] };
  }
}

/**
 * Fetch details for a specific Jira issue by key (e.g. 'PROJ-101').
 */
export async function getJiraIssue(
  issueKey: string
): Promise<{ data: JiraIssue | null }> {
  try {
    const issue = await apiClient<JiraIssue>(
      `/api/jira/issues/${encodeURIComponent(issueKey)}`
    );
    return { data: issue };
  } catch (err) {
    console.warn(`Failed to fetch Jira issue ${issueKey}:`, err);
    return { data: null };
  }
}

/**
 * Fetch normalized Jira evidence deterministically correlated with an incident.
 */
export async function getJiraEvidence(
  incidentId: string
): Promise<{ data: JiraEvidence | null }> {
  try {
    const evidence = await apiClient<JiraEvidence>(
      `/api/jira/evidence/${encodeURIComponent(incidentId)}`
    );
    return { data: evidence };
  } catch (err) {
    console.warn(`Failed to fetch Jira evidence for incident ${incidentId}:`, err);
    return { data: null };
  }
}
