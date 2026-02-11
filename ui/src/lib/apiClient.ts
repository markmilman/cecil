import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type {
  BrowseResponse,
  ScanRequest,
  ScanResponse,
  UploadResponse,
  MappingConfigRequest,
  MappingConfigResponse,
  MappingValidationRequest,
  MappingValidationResult,
  FieldPreviewResponse,
  FieldMappingEntry,
  SampleRecordResponse,
  SanitizeRequest,
  SanitizeResponse,
} from '@/types';

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
   * Upload one or more files to the server for scanning
   *
   * @param files - Array of File objects from a file input
   * @returns Upload response with file metadata and any errors
   * @throws {ApiClientError} If the upload request fails
   */
  async uploadFiles(files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }
    const response = await this.client.post<UploadResponse>(
      '/api/v1/filesystem/upload',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return response.data;
  }

  /**
   * Create a new mapping configuration
   *
   * @param request - Mapping configuration payload
   * @returns Created mapping configuration with ID and policy hash
   * @throws {ApiClientError} If the creation fails
   */
  async createMapping(request: MappingConfigRequest): Promise<MappingConfigResponse> {
    const response = await this.client.post<MappingConfigResponse>(
      '/api/v1/mappings/',
      request,
    );
    return response.data;
  }

  /**
   * List all mapping configurations
   *
   * @returns Array of mapping configurations
   * @throws {ApiClientError} If the request fails
   */
  async listMappings(): Promise<MappingConfigResponse[]> {
    const response = await this.client.get<MappingConfigResponse[]>('/api/v1/mappings/');
    return response.data;
  }

  /**
   * Get a specific mapping configuration by ID
   *
   * @param mappingId - Unique mapping identifier
   * @returns Mapping configuration
   * @throws {ApiClientError} If the mapping is not found
   */
  async getMapping(mappingId: string): Promise<MappingConfigResponse> {
    const response = await this.client.get<MappingConfigResponse>(
      `/api/v1/mappings/${mappingId}`,
    );
    return response.data;
  }

  /**
   * Update an existing mapping configuration
   *
   * @param mappingId - Unique mapping identifier
   * @param request - Updated mapping configuration payload
   * @returns Updated mapping configuration
   * @throws {ApiClientError} If the update fails
   */
  async updateMapping(
    mappingId: string,
    request: MappingConfigRequest,
  ): Promise<MappingConfigResponse> {
    const response = await this.client.put<MappingConfigResponse>(
      `/api/v1/mappings/${mappingId}`,
      request,
    );
    return response.data;
  }

  /**
   * Delete a mapping configuration
   *
   * @param mappingId - Unique mapping identifier
   * @throws {ApiClientError} If the deletion fails
   */
  async deleteMapping(mappingId: string): Promise<void> {
    await this.client.delete(`/api/v1/mappings/${mappingId}`);
  }

  /**
   * Validate a mapping against a sample record
   *
   * @param request - Validation request with mapping and sample record
   * @returns Validation result with matched/unmapped/missing fields
   * @throws {ApiClientError} If the validation request fails
   */
  async validateMapping(request: MappingValidationRequest): Promise<MappingValidationResult> {
    const response = await this.client.post<MappingValidationResult>(
      '/api/v1/mappings/validate',
      request,
    );
    return response.data;
  }

  /**
   * Preview the effect of a mapping on a sample record
   *
   * @param fields - Field mapping entries to preview
   * @param sampleRecord - Sample data record to transform
   * @returns Preview entries showing original and transformed values
   * @throws {ApiClientError} If the preview request fails
   */
  async previewMapping(
    fields: Record<string, FieldMappingEntry>,
    sampleRecord: Record<string, string>,
  ): Promise<FieldPreviewResponse> {
    const response = await this.client.post<FieldPreviewResponse>(
      '/api/v1/mappings/preview',
      { fields, sample_record: sampleRecord },
    );
    return response.data;
  }

  /**
   * Fetch a sample record from a data source for mapping configuration
   *
   * @param source - Path or identifier of the data source
   * @param fileFormat - Optional file format hint
   * @returns Sample record with field names and values
   * @throws {ApiClientError} If the sample record cannot be fetched
   */
  async getSampleRecord(source: string, fileFormat?: string): Promise<SampleRecordResponse> {
    const body: Record<string, string> = { source };
    if (fileFormat) {
      body.file_format = fileFormat;
    }
    const response = await this.client.post<SampleRecordResponse>(
      '/api/v1/mappings/sample',
      body,
    );
    return response.data;
  }

  /**
   * Load a mapping configuration from a YAML file on disk
   */
  async loadMappingYaml(path: string): Promise<MappingConfigResponse> {
    const response = await this.client.post<MappingConfigResponse>(
      '/api/v1/mappings/load-yaml',
      { path },
    );
    return response.data;
  }

  /**
   * Start a sanitization run
   */
  async sanitize(request: SanitizeRequest): Promise<SanitizeResponse> {
    const response = await this.client.post<SanitizeResponse>(
      '/api/v1/scans/sanitize',
      request,
    );
    return response.data;
  }

  /**
   * Open a directory in the system file manager
   *
   * @param path - Absolute path to the directory to open
   * @returns Response indicating success or failure
   * @throws {ApiClientError} If the request fails
   */
  async openDirectory(path: string): Promise<{ success: boolean; message?: string }> {
    const response = await this.client.post<{ success: boolean; message?: string }>(
      '/api/v1/filesystem/open-directory',
      { path },
    );
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
