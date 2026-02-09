"""Scan management API routes.

Provides the POST /api/v1/scans endpoint for initiating file scans
and a background task executor that streams records through the
provider pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

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

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])

# Mapping of file extensions to supported FileFormat enum values.
_EXTENSION_FORMAT_MAP: dict[str, FileFormat] = {
    ".jsonl": FileFormat.JSONL,
    ".csv": FileFormat.CSV,
    ".parquet": FileFormat.PARQUET,
}


@dataclass
class ScanState:
    """Mutable scan state stored in the in-memory scan store.

    Tracks the lifecycle of a single scan operation from creation
    through background execution to completion or failure.
    """

    scan_id: str
    status: ScanStatus
    source: str
    file_format: FileFormat
    created_at: datetime
    records_processed: int = 0
    records_redacted: int = 0
    errors: list[str] = field(default_factory=list)


# In-memory scan store keyed by scan_id.
_scan_store: dict[str, ScanState] = {}


def _scan_state_to_response(state: ScanState) -> ScanResponse:
    """Convert a ScanState dataclass to a ScanResponse Pydantic model.

    Args:
        state: The internal scan state to convert.

    Returns:
        A ScanResponse suitable for API serialization.
    """
    return ScanResponse(
        scan_id=state.scan_id,
        status=state.status,
        source=state.source,
        file_format=state.file_format,
        created_at=state.created_at,
        records_processed=state.records_processed,
        records_redacted=state.records_redacted,
        errors=state.errors,
    )


def _execute_scan(
    scan_id: str,
    source: str,
    file_format: FileFormat,
    provider_id: str,
) -> None:
    """Execute a scan as a background task.

    Connects to the provider, streams all records, and updates the
    scan state with progress and final status.  Errors are captured
    by exception class name only -- never raw data or PII.

    Args:
        scan_id: The unique scan identifier.
        source: The file path to scan.
        file_format: The resolved file format.
        provider_id: The provider identifier for the registry.
    """
    # TODO(#65): Wire SanitizationEngine here -- currently passthrough mode
    state = _scan_store[scan_id]
    state.status = ScanStatus.RUNNING
    logger.info(
        "Scan started",
        extra={"scan_id": scan_id, "provider_id": provider_id},
    )

    provider = get_provider(
        provider_id,
        file_path=source,
        format_hint=file_format.value,
    )
    try:
        provider.connect()
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
    except CecilError as err:
        state.status = ScanStatus.FAILED
        state.errors.append(type(err).__name__)
        logger.warning(
            "Scan failed with CecilError",
            extra={"scan_id": scan_id, "error_type": type(err).__name__},
        )
    except Exception as err:
        state.status = ScanStatus.FAILED
        state.errors.append(type(err).__name__)
        logger.warning(
            "Scan failed with unexpected error",
            extra={"scan_id": scan_id, "error_type": type(err).__name__},
        )
    finally:
        provider.close()


@router.post(
    "/",
    response_model=ScanResponse,
    status_code=201,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
) -> ScanResponse | JSONResponse:
    """Initiate a new file scan.

    Validates the source path, resolves the file format, and queues
    a background task to stream records through the provider pipeline.

    Args:
        request: The scan request payload.
        background_tasks: FastAPI background task manager.

    Returns:
        A ScanResponse with the new scan's metadata, or a JSONResponse
        with an error payload for validation failures.
    """
    # Path traversal check.
    if ".." in Path(request.source).parts:
        logger.warning(
            "Path traversal attempt blocked",
            extra={"source_parts_count": len(Path(request.source).parts)},
        )
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error="path_traversal",
                message="Path traversal is not allowed",
            ).model_dump(),
        )

    # Resolve and validate file existence.
    resolved = Path(request.source).resolve()
    if not resolved.is_file():
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="file_not_found",
                message="Source file does not exist",
            ).model_dump(),
        )

    # Format resolution: explicit or auto-detected.
    if request.file_format is not None:
        file_format = request.file_format
    else:
        suffix = resolved.suffix.lower()
        detected = _EXTENSION_FORMAT_MAP.get(suffix)
        if detected is None:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    error="unsupported_format",
                    message="File format not supported or cannot be auto-detected",
                ).model_dump(),
            )
        file_format = detected

    # Create scan state.
    scan_id = str(uuid4())
    state = ScanState(
        scan_id=scan_id,
        status=ScanStatus.PENDING,
        source=str(resolved),
        file_format=file_format,
        created_at=datetime.now(tz=UTC),
    )
    _scan_store[scan_id] = state

    logger.info(
        "Scan created",
        extra={
            "scan_id": scan_id,
            "file_format": file_format.value,
        },
    )

    # Queue the background scan execution.
    background_tasks.add_task(
        _execute_scan,
        scan_id,
        request.source,
        file_format,
        request.provider_id,
    )

    return _scan_state_to_response(state)
