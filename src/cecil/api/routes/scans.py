"""Scan management API routes.

Provides the POST /api/v1/scans endpoint for initiating file scans,
GET /api/v1/scans/{scan_id} for retrieving scan status, a WebSocket
endpoint for real-time progress streaming, and a background task
executor that streams records through the provider pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from cecil.api.schemas import (
    ErrorResponse,
    FileFormat,
    SanitizeRequest,
    SanitizeResponse,
    ScanProgress,
    ScanRequest,
    ScanResponse,
    ScanStatus,
)
from cecil.core.output.writer import JsonlWriter
from cecil.core.providers.registry import get_provider
from cecil.core.sanitizer.engine import SanitizationEngine
from cecil.core.sanitizer.mapping import MappingParser
from cecil.core.sanitizer.models import MappingConfig
from cecil.core.sanitizer.strategies import StrictStrategy
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
    output_path: str | None = None
    records_sanitized: int = 0
    records_failed: int = 0
    _cancel_event: threading.Event = field(default_factory=threading.Event)


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


def _execute_sanitize(
    scan_id: str,
    source: str,
    file_format: FileFormat,
    mapping_config: MappingConfig,
    output_path: str,
) -> None:
    """Execute sanitization as a background task.

    Connects to the provider, streams records through the sanitization
    engine, and writes sanitized output to the JSONL writer.

    Args:
        scan_id: The unique scan identifier.
        source: The file path to sanitize.
        file_format: The resolved file format.
        mapping_config: The mapping configuration for the strategy.
        output_path: The output file path.
    """
    state = _scan_store[scan_id]
    state.status = ScanStatus.RUNNING

    provider = get_provider("local_file", file_path=source, format_hint=file_format.value)
    strategy = StrictStrategy(config=mapping_config)
    engine = SanitizationEngine(strategy)
    writer = JsonlWriter(Path(output_path))

    try:
        provider.connect()
        for sanitized_record in engine.process_stream(provider.stream_records()):
            # Check for cancellation before processing each record.
            if state._cancel_event.is_set():
                state.status = ScanStatus.CANCELLED
                logger.info(
                    "Sanitization cancelled",
                    extra={"scan_id": scan_id, "records_processed": engine.records_processed},
                )
                return

            writer.write_record(sanitized_record.data)
            state.records_processed = engine.records_processed
            state.records_sanitized = engine.records_sanitized
            state.records_failed = engine.records_failed

        state.status = ScanStatus.COMPLETED
        state.records_processed = engine.records_processed
        state.records_sanitized = engine.records_sanitized
        state.records_failed = engine.records_failed
    except CecilError as err:
        state.status = ScanStatus.FAILED
        state.errors.append(type(err).__name__)
    except Exception as err:
        state.status = ScanStatus.FAILED
        state.errors.append(type(err).__name__)
    finally:
        writer.close()
        provider.close()


@router.post(
    "/sanitize",
    response_model=SanitizeResponse,
    status_code=201,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def sanitize(
    request: SanitizeRequest,
    background_tasks: BackgroundTasks,
) -> SanitizeResponse | JSONResponse:
    """Initiate a sanitization run with a mapping configuration.

    Validates the source path, resolves the mapping, and queues
    a background task to sanitize records through the engine.

    Args:
        request: The sanitize request payload.
        background_tasks: FastAPI background task manager.

    Returns:
        A SanitizeResponse with the new scan's metadata, or a
        JSONResponse with an error payload for validation failures.
    """
    # Path traversal check.
    if ".." in Path(request.source).parts:
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error="path_traversal",
                message="Path traversal is not allowed",
            ).model_dump(),
        )

    # Validate source file.
    resolved = Path(request.source).resolve()
    if not resolved.is_file():
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="file_not_found",
                message="Source file does not exist",
            ).model_dump(),
        )

    # Resolve mapping.
    mapping_config: MappingConfig | None = None
    if request.mapping_id:
        from cecil.api.routes.mappings import _mapping_store

        mapping_state = _mapping_store.get(request.mapping_id)
        if mapping_state is None:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(
                    error="mapping_not_found",
                    message="No mapping found with the given ID",
                ).model_dump(),
            )
        mapping_config = mapping_state.config
    elif request.mapping_yaml_path:
        try:
            mapping_config = MappingParser().parse_file(request.mapping_yaml_path)
        except CecilError as err:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    error="mapping_error",
                    message=str(err),
                ).model_dump(),
            )
    else:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="missing_mapping",
                message="Either mapping_id or mapping_yaml_path is required",
            ).model_dump(),
        )

    # Resolve file format.
    suffix = resolved.suffix.lower()
    detected = _EXTENSION_FORMAT_MAP.get(suffix)
    if detected is None:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="unsupported_format",
                message="File format not supported",
            ).model_dump(),
        )

    # Build output path.
    output_dir = Path(request.output_dir)
    output_path = output_dir / f"{resolved.stem}_sanitized.jsonl"

    # Ensure output directory exists.
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="output_dir_error",
                message=f"Cannot create output directory: {err}",
            ).model_dump(),
        )

    # Create scan state.
    scan_id = str(uuid4())
    state = ScanState(
        scan_id=scan_id,
        status=ScanStatus.PENDING,
        source=str(resolved),
        file_format=detected,
        created_at=datetime.now(tz=UTC),
        output_path=str(output_path),
    )
    _scan_store[scan_id] = state

    # Queue background task.
    background_tasks.add_task(
        _execute_sanitize,
        scan_id,
        str(resolved),
        detected,
        mapping_config,
        str(output_path),
    )

    return SanitizeResponse(
        scan_id=scan_id,
        status=state.status,
        source=str(resolved),
        output_path=str(output_path),
        records_processed=0,
        records_sanitized=0,
        records_failed=0,
        created_at=state.created_at,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_scan(scan_id: str) -> ScanResponse | JSONResponse:
    """Retrieve the current status of a scan.

    Args:
        scan_id: The unique scan identifier.

    Returns:
        A ScanResponse with the scan's current metadata, or a 404
        JSONResponse if no scan matches the given ID.
    """
    state = _scan_store.get(scan_id)
    if state is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="scan_not_found",
                message="No scan found with the given ID",
            ).model_dump(),
        )
    return _scan_state_to_response(state)


@router.post(
    "/{scan_id}/cancel",
    response_model=ScanResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def cancel_scan(scan_id: str) -> ScanResponse | JSONResponse:
    """Cancel a running scan.

    Sets the cancellation flag on the scan, which will be checked
    by the background task on its next iteration. The scan status
    will transition to CANCELLED once the task stops processing.

    Args:
        scan_id: The unique scan identifier.

    Returns:
        A ScanResponse with the scan's current metadata, or a 404
        JSONResponse if no scan matches the given ID, or a 422
        JSONResponse if the scan is not in a cancellable state.
    """
    state = _scan_store.get(scan_id)
    if state is None:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="scan_not_found",
                message="No scan found with the given ID",
            ).model_dump(),
        )

    # Only PENDING or RUNNING scans can be cancelled.
    if state.status not in (ScanStatus.PENDING, ScanStatus.RUNNING):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="scan_not_cancellable",
                message=f"Scan with status '{state.status}' cannot be cancelled",
            ).model_dump(),
        )

    # Set the cancellation flag.
    state._cancel_event.set()
    logger.info(
        "Scan cancellation requested",
        extra={"scan_id": scan_id, "current_status": state.status.value},
    )

    return _scan_state_to_response(state)


@router.websocket("/{scan_id}/ws")
async def scan_progress_ws(websocket: WebSocket, scan_id: str) -> None:
    """Stream real-time scan progress over WebSocket.

    Sends periodic ``ScanProgress`` JSON messages until the scan
    reaches a terminal state (``COMPLETED`` or ``FAILED``), then
    closes the connection.  If the scan ID is unknown the WebSocket
    is closed immediately with code 4004.

    Args:
        websocket: The incoming WebSocket connection.
        scan_id: The unique scan identifier to monitor.
    """
    state = _scan_store.get(scan_id)
    if state is None:
        await websocket.close(code=4004, reason="Scan not found")
        return

    await websocket.accept()
    try:
        while True:
            elapsed = (datetime.now(tz=UTC) - state.created_at).total_seconds()
            progress = ScanProgress(
                scan_id=state.scan_id,
                status=state.status,
                records_processed=state.records_processed,
                total_records=None,
                percent_complete=None,
                elapsed_seconds=elapsed,
                error_type=state.errors[0] if state.errors else None,
            )
            await websocket.send_json(progress.model_dump())

            if state.status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED):
                break

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info(
            "WebSocket client disconnected",
            extra={"scan_id": scan_id},
        )
        return

    await websocket.close()
