"""Scan management routes.

Provides the POST /scans endpoint that accepts a ScanRequest, validates
the source path, creates a scan job backed by an in-memory store, and
launches the scan as a background task via the provider registry.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from cecil.api.schemas import (
    ErrorResponse,
    FileFormat,
    ScanRequest,
    ScanResponse,
    ScanStatus,
)
from cecil.core.providers.registry import get_provider
from cecil.utils.errors import CecilError


logger = logging.getLogger(__name__)

# File extension to FileFormat mapping for auto-detection.
_EXTENSION_FORMAT_MAP: dict[str, FileFormat] = {
    ".jsonl": FileFormat.JSONL,
    ".csv": FileFormat.CSV,
    ".parquet": FileFormat.PARQUET,
}

router = APIRouter(tags=["scans"])


# ── In-memory scan state ──────────────────────────────────────────────


@dataclass
class ScanState:
    """Mutable state for a single scan job.

    Stored in ``scan_store`` and updated in-place by the background
    task as records are streamed through the provider.

    Attributes:
        scan_id: Unique identifier for the scan (UUID4).
        status: Current lifecycle status.
        source: Source identifier (e.g. file path).
        file_format: Detected or explicit file format.
        created_at: Timestamp when the scan was created.
        records_processed: Running count of records streamed.
        records_redacted: Running count of records containing PII.
        errors: Error messages accumulated during the scan.
        start_time: Monotonic clock value when the scan was created.
    """

    scan_id: str
    status: ScanStatus
    source: str
    file_format: FileFormat
    created_at: datetime
    records_processed: int = 0
    records_redacted: int = 0
    errors: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.monotonic)


scan_store: dict[str, ScanState] = {}
"""Module-level in-memory store mapping scan IDs to their mutable state."""


# ── Helper functions ──────────────────────────────────────────────────


def validate_source_path(raw: str) -> Path:
    """Resolve a raw source string to a safe, absolute path.

    Ensures the resolved path does not escape the user's home
    directory, preventing path-traversal attacks.

    Args:
        raw: The raw source path string from the request.

    Returns:
        The resolved absolute ``Path``.

    Raises:
        HTTPException: 403 if the path escapes the home directory.
    """
    resolved = Path(raw).resolve()
    home = Path.home()
    if not resolved.is_relative_to(home):
        logger.warning(
            "Path traversal attempt blocked",
            extra={"raw_path": raw},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error="path_traversal",
                message="Source path must be within the user's home directory",
            ).model_dump(),
        )
    return resolved


def detect_file_format(source: Path) -> FileFormat:
    """Detect the file format from the source path extension.

    Args:
        source: The resolved source file path.

    Returns:
        The detected ``FileFormat``.

    Raises:
        HTTPException: 422 if the file extension is not supported.
    """
    suffix = source.suffix.lower()
    fmt = _EXTENSION_FORMAT_MAP.get(suffix)
    if fmt is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponse(
                error="unsupported_format",
                message=f"Unsupported file extension: '{suffix}'",
                details={"supported": ", ".join(_EXTENSION_FORMAT_MAP.keys())},
            ).model_dump(),
        )
    return fmt


def _run_scan(
    scan_id: str,
    source: Path,
    file_format: FileFormat,
    provider_id: str,
    strategy: str,
) -> None:
    """Execute a scan job as a background task.

    Opens the provider via its context manager, streams all records,
    and updates the scan state in ``scan_store`` as progress is made.
    On success the status is set to ``completed``; on failure it is
    set to ``failed`` with the error message appended.

    Args:
        scan_id: Unique identifier for this scan.
        source: Resolved file path to ingest.
        file_format: The file format to use.
        provider_id: Registry key for the data provider.
        strategy: Sanitization strategy name (reserved for future use).
    """
    state = scan_store[scan_id]
    state.status = ScanStatus.RUNNING

    logger.info(
        "Scan started",
        extra={
            "scan_id": scan_id,
            "provider_id": provider_id,
            "format": file_format.value,
        },
    )

    try:
        provider = get_provider(
            provider_id,
            file_path=str(source),
            format_hint=file_format.value,
        )
        with provider:
            for _record in provider.stream_records():
                state.records_processed += 1

        state.status = ScanStatus.COMPLETED
        logger.info(
            "Scan completed",
            extra={
                "scan_id": scan_id,
                "records_processed": state.records_processed,
            },
        )
    except CecilError as exc:
        state.status = ScanStatus.FAILED
        state.errors.append(str(exc))
        logger.error(
            "Scan failed",
            extra={
                "scan_id": scan_id,
                "error": str(exc),
            },
        )
    except Exception as exc:
        state.status = ScanStatus.FAILED
        state.errors.append(str(exc))
        logger.error(
            "Scan failed with unexpected error",
            extra={
                "scan_id": scan_id,
                "error_type": type(exc).__name__,
            },
        )


# ── Route handler ─────────────────────────────────────────────────────


@router.post(
    "/scans",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        403: {"model": ErrorResponse, "description": "Path traversal detected"},
        404: {"model": ErrorResponse, "description": "Source file not found"},
        422: {"model": ErrorResponse, "description": "Validation error or unsupported format"},
    },
)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
) -> ScanResponse:
    """Create a new scan job.

    Validates the source path, detects file format, stores initial
    scan state, and launches the scan as a background task.

    Args:
        request: The scan request payload.
        background_tasks: FastAPI background task manager.

    Returns:
        A ``ScanResponse`` with status ``pending`` and the assigned scan ID.
    """
    # 1. Validate source path (path traversal protection).
    source = validate_source_path(request.source)

    # 2. Validate source file exists.
    if not source.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error="file_not_found",
                message=f"Source file not found: {source}",
            ).model_dump(),
        )

    # 3. Determine file format (explicit or auto-detect).
    file_format: FileFormat
    if request.file_format is not None:
        file_format = request.file_format
    else:
        file_format = detect_file_format(source)

    # 4. Generate scan ID and store initial state.
    scan_id = str(uuid.uuid4())
    now = datetime.now(tz=UTC)

    state = ScanState(
        scan_id=scan_id,
        status=ScanStatus.PENDING,
        source=str(source),
        file_format=file_format,
        created_at=now,
    )
    scan_store[scan_id] = state

    logger.info(
        "Scan created",
        extra={
            "scan_id": scan_id,
            "source": str(source),
            "file_format": file_format.value,
            "provider_id": request.provider_id,
        },
    )

    # 5. Launch background task.
    background_tasks.add_task(
        _run_scan,
        scan_id=scan_id,
        source=source,
        file_format=file_format,
        provider_id=request.provider_id,
        strategy=request.strategy,
    )

    # 6. Return 201 with pending status.
    return ScanResponse(
        scan_id=scan_id,
        status=ScanStatus.PENDING,
        source=str(source),
        file_format=file_format,
        created_at=now,
        records_processed=0,
        records_redacted=0,
        errors=[],
    )
