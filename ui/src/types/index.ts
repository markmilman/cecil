/**
 * Shared TypeScript type definitions for the Cecil UI
 */

/**
 * Top-level views rendered in the main content area.
 * The app uses state-driven view switching rather than a router.
 */
export type ActiveView = 'dashboard' | 'wizard';

/**
 * Steps within the ingestion wizard flow.
 */
export type WizardStep = 1 | 2 | 3 | 4;

/**
 * Navigation route definition
 */
export interface Route {
  path: string;
  label: string;
  icon?: string;
}

/**
 * API response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

/**
 * Supported file formats for data ingestion
 */
export enum FileFormat {
  JSONL = "jsonl",
  CSV = "csv",
  PARQUET = "parquet",
}

/**
 * Status values for scan operations
 */
export enum ScanStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
}

/**
 * Request payload for initiating a new scan
 */
export interface ScanRequest {
  provider_id?: string; // default: "local_file"
  source: string;
  file_format?: FileFormat | null;
  strategy?: string; // default: "strict"
  output_format?: string; // default: "jsonl"
}

/**
 * Response payload for scan operations
 */
export interface ScanResponse {
  scan_id: string;
  status: ScanStatus;
  source: string;
  file_format: FileFormat;
  created_at: string; // ISO 8601 datetime string
  records_processed: number;
  records_redacted: number;
  errors: string[];
}

/**
 * A single file or directory entry from the filesystem browse endpoint
 */
export interface FilesystemEntry {
  name: string;
  path: string;
  size: number | null;
  modified: string | null; // ISO 8601 datetime string
  is_directory: boolean;
  is_readable: boolean;
  format: FileFormat | null;
}

/**
 * Response from the filesystem browse endpoint
 */
export interface BrowseResponse {
  current_path: string;
  parent_path: string | null;
  directories: FilesystemEntry[];
  files: FilesystemEntry[];
  error: string | null;
}

/**
 * Metadata for a single uploaded file (returned by the upload endpoint)
 */
export interface UploadedFileInfo {
  name: string;
  path: string;
  size: number;
  format: FileFormat | null;
}

/**
 * Response from the file upload endpoint
 */
export interface UploadResponse {
  files: UploadedFileInfo[];
  errors: string[];
}

/**
 * Real-time progress information for an active scan
 */
export interface ScanProgress {
  scan_id: string;
  status: ScanStatus;
  records_processed: number;
  total_records: number | null;
  percent_complete: number | null;
  elapsed_seconds: number;
  error_type: string | null;
}
