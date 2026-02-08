"""Tests for API request and response schemas.

Validates Pydantic v2 models for correct default values, field validation,
and serialization behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cecil.api.schemas import (
    FileFormat,
    ScanProgress,
    ScanRequest,
    ScanResponse,
    ScanStatus,
)


class TestFileFormat:
    """Tests for FileFormat enum."""

    def test_file_format_accepts_jsonl(self) -> None:
        """FileFormat enum accepts 'jsonl' value."""
        assert FileFormat.JSONL == "jsonl"

    def test_file_format_accepts_csv(self) -> None:
        """FileFormat enum accepts 'csv' value."""
        assert FileFormat.CSV == "csv"

    def test_file_format_accepts_parquet(self) -> None:
        """FileFormat enum accepts 'parquet' value."""
        assert FileFormat.PARQUET == "parquet"

    def test_file_format_rejects_unknown_value(self) -> None:
        """FileFormat enum rejects unknown values."""
        with pytest.raises(ValueError):
            FileFormat("unknown")


class TestScanStatus:
    """Tests for ScanStatus enum."""

    def test_scan_status_accepts_pending(self) -> None:
        """ScanStatus enum accepts 'pending' value."""
        assert ScanStatus.PENDING == "pending"

    def test_scan_status_accepts_running(self) -> None:
        """ScanStatus enum accepts 'running' value."""
        assert ScanStatus.RUNNING == "running"

    def test_scan_status_accepts_completed(self) -> None:
        """ScanStatus enum accepts 'completed' value."""
        assert ScanStatus.COMPLETED == "completed"

    def test_scan_status_accepts_failed(self) -> None:
        """ScanStatus enum accepts 'failed' value."""
        assert ScanStatus.FAILED == "failed"

    def test_scan_status_rejects_unknown_value(self) -> None:
        """ScanStatus enum rejects unknown values."""
        with pytest.raises(ValueError):
            ScanStatus("unknown")


class TestScanRequest:
    """Tests for ScanRequest schema."""

    def test_scan_request_validates_source_is_non_empty_string(self) -> None:
        """ScanRequest validates source is non-empty string."""
        # Valid source
        request = ScanRequest(source="/path/to/file.jsonl")
        assert request.source == "/path/to/file.jsonl"

        # Empty string should fail validation
        with pytest.raises(ValidationError):
            ScanRequest(source="")

    def test_scan_request_rejects_whitespace_only_source(self) -> None:
        """ScanRequest rejects whitespace-only source string."""
        with pytest.raises(ValidationError):
            ScanRequest(source="   ")

    def test_scan_request_defaults_provider_id_to_local_file(self) -> None:
        """ScanRequest defaults provider_id to 'local_file'."""
        request = ScanRequest(source="/path/to/file.jsonl")
        assert request.provider_id == "local_file"

    def test_scan_request_defaults_strategy_to_strict(self) -> None:
        """ScanRequest defaults strategy to 'strict'."""
        request = ScanRequest(source="/path/to/file.jsonl")
        assert request.strategy == "strict"

    def test_scan_request_defaults_output_format_to_jsonl(self) -> None:
        """ScanRequest defaults output_format to 'jsonl'."""
        request = ScanRequest(source="/path/to/file.jsonl")
        assert request.output_format == "jsonl"

    def test_scan_request_defaults_file_format_to_none(self) -> None:
        """ScanRequest defaults file_format to None."""
        request = ScanRequest(source="/path/to/file.jsonl")
        assert request.file_format is None

    def test_scan_request_accepts_all_fields(self) -> None:
        """ScanRequest accepts all fields when explicitly provided."""
        request = ScanRequest(
            provider_id="aws_cloudwatch",
            source="/logs/stream-1",
            file_format=FileFormat.CSV,
            strategy="deep_interceptor",
            output_format="csv",
        )
        assert request.provider_id == "aws_cloudwatch"
        assert request.source == "/logs/stream-1"
        assert request.file_format == FileFormat.CSV
        assert request.strategy == "deep_interceptor"
        assert request.output_format == "csv"


class TestScanResponse:
    """Tests for ScanResponse schema."""

    def test_scan_response_defaults_records_processed_to_zero(self) -> None:
        """ScanResponse defaults records_processed to 0."""
        response = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.COMPLETED,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=datetime.now(UTC),
        )
        assert response.records_processed == 0

    def test_scan_response_serializes_errors_as_list(self) -> None:
        """ScanResponse serializes errors as a list."""
        response = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.COMPLETED,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=datetime.now(UTC),
        )
        # Default empty list
        assert response.errors == []
        assert isinstance(response.errors, list)

    def test_scan_response_includes_records_redacted_field(self) -> None:
        """ScanResponse includes records_redacted field."""
        response = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.COMPLETED,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=datetime.now(UTC),
        )
        # Default value is 0
        assert response.records_redacted == 0

        # Can be set explicitly
        response_with_redactions = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.COMPLETED,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=datetime.now(UTC),
            records_redacted=42,
        )
        assert response_with_redactions.records_redacted == 42

    def test_scan_response_errors_default_to_empty_list(self) -> None:
        """ScanResponse errors default to empty list."""
        response = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.COMPLETED,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=datetime.now(UTC),
        )
        assert response.errors == []

    def test_scan_response_accepts_errors_list(self) -> None:
        """ScanResponse accepts errors list when provided."""
        errors = ["Failed to parse line 42", "Memory limit exceeded"]
        response = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.FAILED,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=datetime.now(UTC),
            errors=errors,
        )
        assert response.errors == errors

    def test_scan_response_serializes_all_fields(self) -> None:
        """ScanResponse serializes all fields correctly."""
        created_at = datetime.now(UTC)
        response = ScanResponse(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.RUNNING,
            source="/path/to/file.jsonl",
            file_format=FileFormat.JSONL,
            created_at=created_at,
            records_processed=100,
            records_redacted=15,
            errors=["Warning: skipped malformed line"],
        )
        data = response.model_dump()
        assert data["scan_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["status"] == "running"
        assert data["source"] == "/path/to/file.jsonl"
        assert data["file_format"] == "jsonl"
        assert data["records_processed"] == 100
        assert data["records_redacted"] == 15
        assert data["errors"] == ["Warning: skipped malformed line"]
        assert data["created_at"] == created_at


class TestScanProgress:
    """Tests for ScanProgress schema."""

    def test_scan_progress_accepts_error_type_as_optional_string(self) -> None:
        """ScanProgress accepts error_type as optional string."""
        # Without error_type
        progress = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.RUNNING,
        )
        assert progress.error_type is None

        # With error_type
        progress_with_error = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.FAILED,
            error_type="file_not_found",
        )
        assert progress_with_error.error_type == "file_not_found"

    def test_scan_progress_defaults_records_processed_to_zero(self) -> None:
        """ScanProgress defaults records_processed to 0."""
        progress = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.PENDING,
        )
        assert progress.records_processed == 0

    def test_scan_progress_defaults_total_records_to_none(self) -> None:
        """ScanProgress defaults total_records to None."""
        progress = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.RUNNING,
        )
        assert progress.total_records is None

    def test_scan_progress_defaults_percent_complete_to_none(self) -> None:
        """ScanProgress defaults percent_complete to None."""
        progress = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.RUNNING,
        )
        assert progress.percent_complete is None

    def test_scan_progress_defaults_elapsed_seconds_to_zero(self) -> None:
        """ScanProgress defaults elapsed_seconds to 0.0."""
        progress = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.PENDING,
        )
        assert progress.elapsed_seconds == 0.0

    def test_scan_progress_serializes_all_fields(self) -> None:
        """ScanProgress serializes all fields correctly."""
        progress = ScanProgress(
            scan_id="550e8400-e29b-41d4-a716-446655440000",
            status=ScanStatus.RUNNING,
            records_processed=500,
            total_records=1000,
            percent_complete=50.0,
            elapsed_seconds=12.5,
            error_type=None,
        )
        data = progress.model_dump()
        assert data["scan_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["status"] == "running"
        assert data["records_processed"] == 500
        assert data["total_records"] == 1000
        assert data["percent_complete"] == 50.0
        assert data["elapsed_seconds"] == 12.5
        assert data["error_type"] is None

    def test_scan_progress_accepts_machine_readable_error_codes(self) -> None:
        """ScanProgress accepts machine-readable error codes."""
        error_codes = ["file_not_found", "parse_error", "memory_exceeded"]
        for error_code in error_codes:
            progress = ScanProgress(
                scan_id="550e8400-e29b-41d4-a716-446655440000",
                status=ScanStatus.FAILED,
                error_type=error_code,
            )
            assert progress.error_type == error_code
