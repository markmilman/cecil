/**
 * Shared TypeScript type definitions for the Cecil UI
 */

/**
 * Top-level views rendered in the main content area.
 * The app uses state-driven view switching rather than a router.
 */
export type ActiveView = 'dashboard' | 'wizard' | 'mapping' | 'ingest';

/**
 * Steps within the ingestion wizard flow.
 */
export type WizardStep = 1 | 2 | 3 | 4 | 5;

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

/**
 * Available redaction actions for field-level sanitization
 */
export enum RedactionAction {
  REDACT = "redact",
  MASK = "mask",
  HASH = "hash",
  KEEP = "keep",
}

/**
 * A single field's mapping configuration
 */
export interface FieldMappingEntry {
  action: RedactionAction;
  options: Record<string, string>;
}

/**
 * Request payload for creating or updating a mapping configuration
 */
export interface MappingConfigRequest {
  version: number;
  default_action: RedactionAction;
  fields: Record<string, FieldMappingEntry>;
  name?: string;
}

/**
 * Response payload for a mapping configuration
 */
export interface MappingConfigResponse {
  mapping_id: string;
  version: number;
  default_action: RedactionAction;
  fields: Record<string, FieldMappingEntry>;
  policy_hash: string;
  field_count: number;
  created_at: string;
  yaml_path?: string | null;
  name: string;
}

/**
 * Request payload for validating a mapping against a sample record
 */
export interface MappingValidationRequest {
  mapping: MappingConfigRequest;
  sample_record: Record<string, string>;
}

/**
 * Result of mapping validation
 */
export interface MappingValidationResult {
  is_valid: boolean;
  matched_fields: string[];
  unmapped_fields: string[];
  missing_fields: string[];
}

/**
 * A single field's preview showing original and transformed values
 */
export interface FieldPreviewEntry {
  field_name: string;
  original: string;
  transformed: string;
  action: RedactionAction;
}

/**
 * Response payload for a mapping preview
 */
export interface FieldPreviewResponse {
  entries: FieldPreviewEntry[];
}

/**
 * Response payload for fetching a sample record from a data source
 */
export interface SampleRecordResponse {
  record: Record<string, string>;
  field_count: number;
  source: string;
}

/**
 * Request payload for initiating a sanitization run
 */
export interface SanitizeRequest {
  source: string;
  mapping_id?: string | null;
  mapping_yaml_path?: string | null;
  output_dir: string;
  output_format?: string;
}

/**
 * Response payload for a sanitization run
 */
export interface SanitizeResponse {
  scan_id: string;
  status: ScanStatus;
  source: string;
  output_path: string;
  records_processed: number;
  records_sanitized: number;
  records_failed: number;
  created_at: string;
}
