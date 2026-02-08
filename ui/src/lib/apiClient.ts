import axios, { type AxiosInstance, type AxiosError } from 'axios';

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
   * Get the underlying Axios instance for custom requests
   *
   * @returns The configured Axios instance
   */
  getClient(): AxiosInstance {
    return this.client;
  }
}

/**
 * Default API client instance
 *
 * This instance can be imported and used throughout the application.
 * The port can be overridden via environment variables if needed.
 */
export const apiClient = new ApiClient({
  port: Number(import.meta.env.VITE_API_PORT) || 8000,
});
