import { apiClient } from './client';
import {
  GitHubStatus,
  GitHubRepository,
  GitHubCommitSummary,
  GitHubCommitDetail,
} from '@/types';

/**
 * Fetch GitHub integration status (configuration, API reachability, and rate limit status).
 * Always safe; returns null if the backend or GitHub API is unreachable.
 */
export async function getGitHubStatus(): Promise<{ data: GitHubStatus | null }> {
  try {
    const status = await apiClient<GitHubStatus>('/api/github/status');
    return { data: status };
  } catch (err) {
    console.warn('Failed to fetch GitHub status:', err);
    return { data: null };
  }
}

/**
 * Fetch connected GitHub repository metadata.
 */
export async function getGitHubRepo(): Promise<{ data: GitHubRepository | null }> {
  try {
    const repo = await apiClient<GitHubRepository>('/api/github/repo');
    return { data: repo };
  } catch (err) {
    console.warn('Failed to fetch GitHub repository details:', err);
    return { data: null };
  }
}

/**
 * Fetch recent commit history for the configured repository.
 */
export async function getRecentCommits(limit = 30): Promise<{ data: GitHubCommitSummary[] }> {
  try {
    const commits = await apiClient<GitHubCommitSummary[]>(`/api/github/commits?limit=${limit}`);
    return { data: commits || [] };
  } catch (err) {
    console.warn('Failed to fetch recent GitHub commits:', err);
    return { data: [] };
  }
}

/**
 * Fetch single commit detailed metadata including diff stats and changed files.
 */
export async function getCommitDetail(sha: string): Promise<{ data: GitHubCommitDetail | null }> {
  try {
    const detail = await apiClient<GitHubCommitDetail>(`/api/github/commits/${encodeURIComponent(sha)}`);
    return { data: detail };
  } catch (err) {
    console.warn(`Failed to fetch commit detail for ${sha}:`, err);
    return { data: null };
  }
}
