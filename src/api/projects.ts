/**
 * Project, Application, and Environment Topology API Client
 * Centralizes management of software hierarchy, API keys, and connection guides.
 */

import { apiClient } from './client';
import {
  Project,
  Application,
  Environment,
  EnvironmentApiKeyRegenerateResponse,
  ConnectionGuide,
  IngestionTestResult,
} from '@/types';

// ==========================================
// Project API
// ==========================================

export async function getProjects(): Promise<{ data: Project[] }> {
  try {
    const projects = await apiClient<Project[]>('/api/projects');
    return { data: projects || [] };
  } catch (err) {
    console.warn('Failed to fetch projects:', err);
    return { data: [] };
  }
}

export async function createProject(payload: {
  name: string;
  slug?: string;
  description?: string;
}): Promise<Project> {
  return await apiClient<Project>('/api/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient<void>(`/api/projects/${projectId}`, {
    method: 'DELETE',
  });
}

// ==========================================
// Application API
// ==========================================

export async function getApplications(projectId: string): Promise<{ data: Application[] }> {
  try {
    const apps = await apiClient<Application[]>(`/api/projects/${projectId}/applications`);
    return { data: apps || [] };
  } catch (err) {
    console.warn(`Failed to fetch applications for project ${projectId}:`, err);
    return { data: [] };
  }
}

export async function createApplication(
  projectId: string,
  payload: {
    name: string;
    slug?: string;
    description?: string;
    language: string;
    framework?: string;
    repo_owner?: string;
    repo_name?: string;
    default_branch?: string;
  }
): Promise<Application> {
  return await apiClient<Application>(`/api/projects/${projectId}/applications`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deleteApplication(applicationId: string): Promise<void> {
  await apiClient<void>(`/api/applications/${applicationId}`, {
    method: 'DELETE',
  });
}

// ==========================================
// Environment API
// ==========================================

export async function getEnvironments(applicationId: string): Promise<{ data: Environment[] }> {
  try {
    const envs = await apiClient<Environment[]>(`/api/applications/${applicationId}/environments`);
    return { data: envs || [] };
  } catch (err) {
    console.warn(`Failed to fetch environments for application ${applicationId}:`, err);
    return { data: [] };
  }
}

export async function createEnvironment(
  applicationId: string,
  payload: {
    name: string;
    slug?: string;
    endpoint_url?: string;
    current_commit?: string;
    is_production?: boolean;
  }
): Promise<Environment> {
  return await apiClient<Environment>(`/api/applications/${applicationId}/environments`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getEnvironment(environmentId: string): Promise<{ data: Environment | null }> {
  try {
    const env = await apiClient<Environment>(`/api/environments/${environmentId}`);
    return { data: env };
  } catch (err) {
    console.warn(`Failed to fetch environment ${environmentId}:`, err);
    return { data: null };
  }
}

export async function regenerateEnvironmentKey(
  environmentId: string
): Promise<EnvironmentApiKeyRegenerateResponse> {
  return await apiClient<EnvironmentApiKeyRegenerateResponse>(
    `/api/environments/${environmentId}/regenerate-key`,
    {
      method: 'POST',
    }
  );
}

export async function deleteEnvironment(environmentId: string): Promise<void> {
  await apiClient<void>(`/api/environments/${environmentId}`, {
    method: 'DELETE',
  });
}

// ==========================================
// Connection Guide & Ingestion Test
// ==========================================

export async function getConnectionGuide(environmentId: string): Promise<{ data: ConnectionGuide | null }> {
  try {
    const guide = await apiClient<ConnectionGuide>(`/api/environments/${environmentId}/connection-guide`);
    return { data: guide };
  } catch (err) {
    console.warn(`Failed to fetch connection guide for environment ${environmentId}:`, err);
    return { data: null };
  }
}

export async function testEnvironmentIngestion(environmentId: string): Promise<IngestionTestResult> {
  return await apiClient<IngestionTestResult>(`/api/environments/${environmentId}/test-ingestion`, {
    method: 'POST',
  });
}
