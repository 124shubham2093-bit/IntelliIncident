import { apiClient } from './client';
import {
  SentryStatus,
  SentryProject,
  SentryIssue,
  SentryEvent,
  SentryEvidence,
} from '@/types';

/**
 * Fetch Sentry integration status (configuration, API reachability, and rate limit status).
 * Safe endpoint: never throws and never exposes auth tokens.
 */
export async function getSentryStatus(): Promise<{ data: SentryStatus | null }> {
  try {
    const status = await apiClient<SentryStatus>('/api/sentry/status');
    return { data: status };
  } catch (err) {
    console.warn('Failed to fetch Sentry status:', err);
    return { data: null };
  }
}

/**
 * Fetch configured Sentry project metadata.
 */
export async function getSentryProject(): Promise<{ data: SentryProject | null }> {
  try {
    const project = await apiClient<SentryProject>('/api/sentry/project');
    return { data: project };
  } catch (err) {
    console.warn('Failed to fetch Sentry project details:', err);
    return { data: null };
  }
}

/**
 * Fetch runtime error issues for the configured Sentry project.
 */
export async function getSentryIssues(
  query = 'is:unresolved',
  limit = 10
): Promise<{ data: SentryIssue[] }> {
  try {
    const params = new URLSearchParams({ query, limit: String(limit) });
    const issues = await apiClient<SentryIssue[]>(`/api/sentry/issues?${params.toString()}`);
    return { data: issues || [] };
  } catch (err) {
    console.warn('Failed to fetch Sentry issues:', err);
    return { data: [] };
  }
}

/**
 * Fetch details for a specific Sentry issue.
 */
export async function getSentryIssue(issueId: string): Promise<{ data: SentryIssue | null }> {
  try {
    const issue = await apiClient<SentryIssue>(`/api/sentry/issues/${encodeURIComponent(issueId)}`);
    return { data: issue };
  } catch (err) {
    console.warn(`Failed to fetch Sentry issue ${issueId}:`, err);
    return { data: null };
  }
}

/**
 * Fetch events and stack traces for a specific Sentry issue.
 */
export async function getSentryIssueEvents(
  issueId: string,
  limit = 5
): Promise<{ data: SentryEvent[] }> {
  try {
    const events = await apiClient<SentryEvent[]>(
      `/api/sentry/issues/${encodeURIComponent(issueId)}/events?limit=${limit}`
    );
    return { data: events || [] };
  } catch (err) {
    console.warn(`Failed to fetch Sentry events for issue ${issueId}:`, err);
    return { data: [] };
  }
}

/**
 * Fetch normalized runtime error evidence for RCA correlation.
 */
export async function getSentryEvidence(
  service?: string,
  environment?: string,
  release?: string
): Promise<{ data: SentryEvidence | null }> {
  try {
    const params = new URLSearchParams();
    if (service) params.set('service', service);
    if (environment) params.set('environment', environment);
    if (release) params.set('release', release);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const evidence = await apiClient<SentryEvidence>(`/api/sentry/evidence${queryStr}`);
    return { data: evidence };
  } catch (err) {
    console.warn('Failed to fetch Sentry runtime evidence:', err);
    return { data: null };
  }
}
