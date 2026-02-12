"""API request and response schemas.

Defines Pydantic v2 models used by FastAPI endpoints for request
validation and response serialization.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str = Field(description="Server status indicator")
    version: str = Field(description="Cecil version string")


class ErrorResponse(BaseModel):
    """Consistent error response format for all API endpoints."""

    error: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, str] | None = Field(
        default=None,
        description="Additional context about the error",
    )


class FileFormat(StrEnum):
    """Supported file formats for data ingestion."""

    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"


class ScanStatus(StrEnum):
    """Status values for scan operations."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanRequest(BaseModel):
    """Request payload for initiating a new scan."""

    provider_id: str = Field(
        default="local_file",
        description="Data provider identifier (default: local_file, extensible for cloud providers)",
    )
    source: str = Field(description="Source identifier (e.g., file path for local_file provider)")
    file_format: FileFormat | None = Field(
        default=None,
        description="File format; auto-detected from extension if omitted",
    )
    strategy: str = Field(
        default="strict",
        description="Sanitization strategy to apply (default: strict)",
    )
    output_format: str = Field(
        default="jsonl",
        description="Output format for sanitized data (default: jsonl)",
    )

    @field_validator("source")
    @classmethod
    def validate_source_non_empty(cls, v: str) -> str:
        """Validate that source is not an empty string."""
        if not v or not v.strip():
            raise ValueError("source must be a non-empty string")
        return v


class ScanResponse(BaseModel):
    """Response payload for scan operations."""

    scan_id: str = Field(description="Unique scan identifier (UUID)")
    status: ScanStatus = Field(description="Current scan status")
    source: str = Field(description="Source identifier used for this scan")
    file_format: FileFormat = Field(description="File format used for this scan")
    created_at: datetime = Field(description="Timestamp when the scan was created")
    records_processed: int = Field(
        default=0,
        description="Number of records processed so far",
    )
    records_redacted: int = Field(
        default=0,
        description="Number of records containing PII detections",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of errors encountered during scan (supports partial failure reporting)",
    )


class FilesystemEntry(BaseModel):
    """A single file or directory entry returned by the filesystem browse endpoint."""

    name: str = Field(description="File or directory name")
    path: str = Field(description="Absolute path to the entry")
    size: int | None = Field(
        default=None,
        description="File size in bytes (None for directories)",
    )
    modified: datetime | None = Field(
        default=None,
        description="Last modified timestamp (None if unavailable)",
    )
    is_directory: bool = Field(description="Whether the entry is a directory")
    is_readable: bool = Field(
        default=True,
        description="Whether the entry can be read by the current user",
    )
    format: FileFormat | None = Field(
        default=None,
        description="Detected file format for supported extensions (None for dirs or unknown)",
    )


class BrowseResponse(BaseModel):
    """Response from the filesystem browse endpoint."""

    current_path: str = Field(description="Absolute path of the browsed directory")
    parent_path: str | None = Field(
        default=None,
        description="Absolute path of the parent directory (None for root)",
    )
    directories: list[FilesystemEntry] = Field(
        default_factory=list,
        description="List of subdirectory entries",
    )
    files: list[FilesystemEntry] = Field(
        default_factory=list,
        description="List of file entries (filtered by supported formats unless show_all)",
    )
    error: str | None = Field(
        default=None,
        description="Human-readable error message if browsing failed",
    )


class UploadedFileInfo(BaseModel):
    """Metadata for a single uploaded file."""

    name: str = Field(description="Original filename")
    path: str = Field(description="Server-side path where the file was saved")
    size: int = Field(description="File size in bytes")
    format: FileFormat | None = Field(
        default=None,
        description="Detected file format from extension",
    )


class UploadResponse(BaseModel):
    """Response from the file upload endpoint."""

    files: list[UploadedFileInfo] = Field(
        default_factory=list,
        description="List of successfully uploaded files",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of files that failed to upload (unsupported format, etc.)",
    )


class OpenDirectoryRequest(BaseModel):
    """Request payload for opening a directory in the system file manager."""

    path: str = Field(description="Absolute path to the directory to open")

    @field_validator("path")
    @classmethod
    def validate_path_non_empty(cls, v: str) -> str:
        """Validate that path is not an empty string."""
        if not v or not v.strip():
            raise ValueError("path must be a non-empty string")
        return v


class OpenDirectoryResponse(BaseModel):
    """Response from the open-directory endpoint."""

    success: bool = Field(description="Whether the directory was opened successfully")
    message: str | None = Field(
        default=None,
        description="Human-readable message (error details if success=false)",
    )


class ScanProgress(BaseModel):
    """Real-time progress information for an active scan."""

    scan_id: str = Field(description="Unique scan identifier (UUID)")
    status: ScanStatus = Field(description="Current scan status")
    records_processed: int = Field(
        default=0,
        description="Number of records processed so far",
    )
    total_records: int | None = Field(
        default=None,
        description="Estimated total number of records (may be None for streaming sources)",
    )
    percent_complete: float | None = Field(
        default=None,
        description="Percentage complete (0-100), calculated if total_records is known",
    )
    elapsed_seconds: float = Field(
        default=0.0,
        description="Elapsed time since scan started",
    )
    error_type: str | None = Field(
        default=None,
        description="Machine-readable error code (e.g., file_not_found, parse_error, memory_exceeded)",
    )


# ── Mapping schemas ───────────────────────────────────────────────────


class RedactionActionSchema(StrEnum):
    """Redaction actions available for field mappings."""

    REDACT = "redact"
    MASK = "mask"
    HASH = "hash"
    KEEP = "keep"


class FieldMappingEntrySchema(BaseModel):
    """Configuration for a single field in a mapping."""

    action: RedactionActionSchema = Field(description="Redaction action to apply to this field")
    options: dict[str, str] = Field(
        default_factory=dict,
        description="Action-specific options (e.g., preserve_domain for MASK)",
    )


class MappingConfigRequest(BaseModel):
    """Request payload for creating or updating a mapping configuration."""

    version: int = Field(default=1, description="Mapping schema version")
    default_action: RedactionActionSchema = Field(
        default=RedactionActionSchema.REDACT,
        description="Action to apply to unmapped fields",
    )
    fields: dict[str, FieldMappingEntrySchema] = Field(
        description="Field-level redaction action assignments",
    )
    name: str | None = Field(
        default=None,
        description="Human-readable name for the mapping (auto-generated if not provided)",
    )


class MappingConfigResponse(BaseModel):
    """Response payload for a stored mapping configuration."""

    mapping_id: str = Field(description="Unique mapping identifier (UUID)")
    version: int = Field(description="Mapping schema version")
    default_action: RedactionActionSchema = Field(
        description="Action applied to unmapped fields",
    )
    fields: dict[str, FieldMappingEntrySchema] = Field(
        description="Field-level redaction action assignments",
    )
    policy_hash: str = Field(description="SHA-256 hash of the mapping policy")
    created_at: datetime = Field(description="Timestamp when the mapping was created")
    yaml_path: str | None = Field(
        default=None,
        description="Path to the persisted YAML file on disk (if saved)",
    )
    name: str = Field(description="Human-readable name for the mapping")


class MappingValidationRequest(BaseModel):
    """Request payload for validating a mapping against a sample record."""

    mapping: MappingConfigRequest = Field(description="Mapping configuration to validate")
    sample_record: dict[str, str] = Field(
        description="Sample record to validate the mapping against",
    )


class MappingValidationResponse(BaseModel):
    """Response payload for mapping validation results."""

    is_valid: bool = Field(description="Whether the mapping is valid against the sample record")
    matched_fields: list[str] = Field(
        description="Fields present in both mapping and record",
    )
    unmapped_fields: list[str] = Field(
        description="Fields in the record but not in the mapping",
    )
    missing_fields: list[str] = Field(
        description="Fields in the mapping but not in the record",
    )


class FieldPreviewRequest(BaseModel):
    """Request payload for previewing redaction actions on sample data."""

    fields: dict[str, FieldMappingEntrySchema] = Field(
        description="Field-level redaction action assignments to preview",
    )
    sample_record: dict[str, str] = Field(
        description="Sample record to apply actions on",
    )


class FieldPreviewEntry(BaseModel):
    """A single field's preview showing original and transformed values."""

    field_name: str = Field(description="Name of the field")
    original: str = Field(description="Original value (truncated for Safe-Pipe compliance)")
    transformed: str = Field(description="Value after applying the redaction action")
    action: RedactionActionSchema = Field(description="Redaction action that was applied")


class FieldPreviewResponse(BaseModel):
    """Response payload for field preview results."""

    entries: list[FieldPreviewEntry] = Field(
        description="Preview entries for each field in the sample record",
    )


class SampleRecordRequest(BaseModel):
    """Request payload for reading a sample record from a file."""

    source: str = Field(description="Path to the source file")
    file_format: FileFormat | None = Field(
        default=None,
        description="File format; auto-detected from extension if omitted",
    )


class SampleRecordResponse(BaseModel):
    """Response payload containing a sample record from a file."""

    record: dict[str, str] = Field(
        description="First record from the file (all values as strings, truncated to 200 chars)",
    )
    field_count: int = Field(description="Number of fields in the record")
    source: str = Field(description="Path to the source file")


class SanitizeRequest(BaseModel):
    """Request payload for initiating a sanitization run."""

    source: str = Field(description="Path to the source file to sanitize")
    mapping_id: str | None = Field(
        default=None,
        description="ID of an in-memory mapping",
    )
    mapping_yaml_path: str | None = Field(
        default=None,
        description="Path to a mapping.yaml file on disk",
    )
    output_dir: str = Field(description="Output directory path")
    output_format: str = Field(
        default="jsonl",
        description="Output format (currently only jsonl)",
    )

    @field_validator("source")
    @classmethod
    def validate_source_non_empty(cls, v: str) -> str:
        """Validate that source is not an empty string."""
        if not v or not v.strip():
            raise ValueError("source must be a non-empty string")
        return v


class SanitizeResponse(BaseModel):
    """Response payload for a sanitization run."""

    scan_id: str = Field(description="Unique scan identifier (UUID)")
    status: ScanStatus = Field(description="Current scan status")
    source: str = Field(description="Source file path")
    output_path: str = Field(description="Path to the output file")
    records_processed: int = Field(default=0, description="Records processed")
    records_sanitized: int = Field(
        default=0,
        description="Records successfully sanitized",
    )
    records_failed: int = Field(default=0, description="Records that failed")
    created_at: datetime = Field(description="Timestamp")


class LoadMappingYamlRequest(BaseModel):
    """Request payload for loading a mapping from a YAML file."""

    path: str = Field(description="Path to the mapping.yaml file on disk")


class LoadMappingYamlContentRequest(BaseModel):
    """Request payload for loading a mapping from raw YAML content."""

    content: str = Field(description="Raw YAML content of the mapping file")
    name: str | None = Field(
        default=None,
        description="Human-readable name for the mapping (auto-generated if not provided)",
    )
