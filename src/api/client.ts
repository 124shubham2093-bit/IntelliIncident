/**
 * Core API Client for IntelliIncident
 * Centralizes request handling, base URL configuration, and error wrapping.
 * When the backend is disconnected, it logs and throws structured errors
 * that allow service repositories to serve fallback demo data.
 */

export const API_BASE_URL: string =
  (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status?: number;
  data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 4000, ...customConfig } = options;

  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(customConfig.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...customConfig,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new ApiError(
        `API request failed with status ${response.status}`,
        response.status,
        errorData
      );
    }

    return (await response.json()) as T;
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    const err = error as { name?: string; message?: string };
    if (err?.name === 'AbortError') {
      throw new ApiError(`Request timeout after ${timeoutMs}ms to ${url}`, 408);
    }
    throw new ApiError(`Network error reaching backend: ${err?.message || 'Connection refused'}`, 0);
  }
}
