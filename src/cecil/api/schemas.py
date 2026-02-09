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
