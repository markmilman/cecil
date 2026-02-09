import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type { BrowseResponse, ScanRequest, ScanResponse } from '@/types';

/**
 * Configuration for the API client
 */
interface ApiClientConfig {
  baseURL?: string;
  port?: number;
  timeout?: number;
}

/**
 * Health check response from the FastAPI server
 */
interface HealthCheckResponse {
  status: string;
  timestamp: string;
}

/**
 * API error response structure
 */
interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Custom error class for API client errors
 */
export class ApiClientError extends Error {
  public readonly statusCode?: number;
  public readonly errorResponse?: ApiErrorResponse;

  constructor(message: string, statusCode?: number, errorResponse?: ApiErrorResponse) {
    super(message);
    this.name = 'ApiClientError';
    this.statusCode = statusCode;
    this.errorResponse = errorResponse;
  }
}

/**
 * API client for communicating with the local FastAPI server
 *
 * This client is configured to communicate with the Cecil FastAPI backend
 * running on localhost. The server binds to 127.0.0.1 only for security.
 */
export class ApiClient {
  private readonly client: AxiosInstance;

  constructor(config: ApiClientConfig = {}) {
    const { baseURL, port = 8000, timeout = 10000 } = config;
    const finalBaseURL = baseURL || `http://127.0.0.1:${port}`;

    this.client = axios.create({
      baseURL: finalBaseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiErrorResponse>) => {
        if (error.response) {
          // Server responded with error status
          const { status, data } = error.response;
          throw new ApiClientError(
            data.message || error.message,
            status,
            data
          );
        } else if (error.request) {
          // Request made but no response received
          throw new ApiClientError(
            'No response from server. Is the Cecil backend running?',
            undefined,
            undefined
          );
        } else {
          // Error setting up the request
          throw new ApiClientError(error.message);
        }
      }
    );
  }

  /**
   * Perform a health check on the FastAPI server
   *
   * @returns Health check response with status and timestamp
   * @throws {ApiClientError} If the health check fails
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/v1/health');
    return response.data;
  }

  /**
   * Create a new scan operation
   *
   * @param request - Scan request payload
   * @returns Scan response with scan ID and initial status
   * @throws {ApiClientError} If the scan creation fails
   */
  async createScan(request: ScanRequest): Promise<ScanResponse> {
    const response = await this.client.post<ScanResponse>('/api/v1/scans', request);
    return response.data;
  }

  /**
   * Get the status and details of an existing scan
   *
   * @param scanId - Unique scan identifier
   * @returns Scan response with current status and progress
   * @throws {ApiClientError} If the scan retrieval fails
   */
  async getScan(scanId: string): Promise<ScanResponse> {
    const response = await this.client.get<ScanResponse>(`/api/v1/scans/${scanId}`);
    return response.data;
  }

  /**
   * Browse the filesystem for directories and files
   *
   * @param path - Directory path to browse (defaults to home directory)
   * @param showAll - Include files with unsupported extensions
   * @returns Browse response with directories and files
   * @throws {ApiClientError} If the browse request fails
   */
  async browsePath(path?: string, showAll?: boolean): Promise<BrowseResponse> {
    const params: Record<string, string> = {};
    if (path !== undefined) {
      params.path = path;
    }
    if (showAll !== undefined) {
      params.show_all = String(showAll);
    }
    const response = await this.client.get<BrowseResponse>('/api/v1/filesystem/browse', {
      params,
    });
    return response.data;
  }

  /**
   * Get the underlying Axios instance for custom requests
   *
   * @returns The configured Axios instance
   */
  getClient(): AxiosInstance {
    return this.client;
  }
}

/**
 * Detect the API base URL at runtime.
 *
 * When the React app is served by the FastAPI backend (production /
 * single-binary mode), the API lives on the same origin — so the base
 * URL is simply the current origin.  During Vite dev-server development
 * the frontend runs on a different port and must be told where the API
 * is via the ``VITE_API_PORT`` env var (defaults to 8000).
 */
function detectBaseURL(): string {
  const envPort = import.meta.env.VITE_API_PORT;
  if (envPort) {
    return `http://127.0.0.1:${envPort}`;
  }

  // Served by FastAPI on the same origin — use relative URLs.
  if (typeof window !== 'undefined' && window.location.protocol.startsWith('http')) {
    return window.location.origin;
  }

  return 'http://127.0.0.1:8000';
}

/**
 * Default API client instance
 *
 * When served from the Cecil binary the API is on the same origin;
 * during development ``VITE_API_PORT`` overrides the port.
 */
export const apiClient = new ApiClient({
  baseURL: detectBaseURL(),
});
