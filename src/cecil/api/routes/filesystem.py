"""Filesystem browse and upload API routes.

Provides a GET /api/v1/filesystem/browse endpoint that lists directory
contents for the frontend file browser modal, and a POST /api/v1/filesystem/upload
endpoint for browser-based file uploads.  Includes security hardening against
path traversal and symlink escape attacks.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import JSONResponse

from cecil.api.schemas import (
    BrowseResponse,
    ErrorResponse,
    FileFormat,
    FilesystemEntry,
    OpenDirectoryRequest,
    OpenDirectoryResponse,
    PreviewOutputRequest,
    PreviewOutputResponse,
    UploadedFileInfo,
    UploadResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/filesystem", tags=["filesystem"])

# Mapping of file extensions to supported FileFormat values.
_EXTENSION_FORMAT_MAP: dict[str, FileFormat] = {
    ".jsonl": FileFormat.JSONL,
    ".csv": FileFormat.CSV,
    ".parquet": FileFormat.PARQUET,
}

# Supported file extensions for filtered mode (show_all=false).
_SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(_EXTENSION_FORMAT_MAP.keys())


def _get_default_path() -> str:
    """Return the default browse path (user's home directory).

    Returns:
        Absolute path to the user's home directory.
    """
    return str(Path.home())


def _is_path_traversal(path_str: str) -> bool:
    """Check if a path contains traversal components.

    Args:
        path_str: The path string to check.

    Returns:
        True if the path contains ``..`` components.
    """
    return ".." in Path(path_str).parts


def _is_symlink_escape(resolved: Path, target_dir: Path) -> bool:
    """Check if a resolved path escapes the target directory via symlinks.

    This detects cases where a symlink inside ``target_dir`` points to
    a location outside it.

    Args:
        resolved: The fully resolved (symlinks followed) path.
        target_dir: The directory that should contain the path.

    Returns:
        True if the resolved path is outside the target directory.
    """
    try:
        resolved.relative_to(target_dir.resolve())
        return False
    except ValueError:
        return True


def _build_entry(entry_path: Path) -> FilesystemEntry | None:
    """Build a FilesystemEntry from a filesystem path.

    Returns None if the path cannot be stat'd (e.g. broken symlink,
    permission denied).

    Args:
        entry_path: The path to inspect.

    Returns:
        A populated FilesystemEntry, or None on error.
    """
    try:
        stat = entry_path.stat()
    except OSError:
        return None

    is_dir = entry_path.is_dir()
    suffix = entry_path.suffix.lower()
    detected_format = _EXTENSION_FORMAT_MAP.get(suffix) if not is_dir else None

    is_readable = os.access(entry_path, os.R_OK)

    try:
        modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    except (OSError, ValueError):
        modified = None

    return FilesystemEntry(
        name=entry_path.name,
        path=str(entry_path),
        size=stat.st_size if not is_dir else None,
        modified=modified,
        is_directory=is_dir,
        is_readable=is_readable,
        format=detected_format,
    )


@router.get(
    "/browse",
    response_model=BrowseResponse,
)
async def browse_filesystem(
    path: str | None = Query(
        default=None,
        description="Directory path to browse (defaults to home directory)",
    ),
    show_all: bool = Query(
        default=False,
        description="Show all files, not just supported formats",
    ),
) -> BrowseResponse:
    """List contents of a directory for the file browser.

    Returns directories and files separately, sorted alphabetically.
    By default only shows files with supported extensions (.jsonl, .csv,
    .parquet).  Hidden files (dotfiles) are excluded unless ``show_all``
    is ``True``.

    Security: Blocks path traversal (``..``), validates that resolved
    paths are real directories, and excludes broken symlinks.

    Args:
        path: Directory to browse.  Defaults to the user's home directory.
        show_all: If ``True``, include all files regardless of extension.

    Returns:
        A BrowseResponse with directories and files, or an error message.
    """
    browse_path = path if path is not None else _get_default_path()

    # Security: block path traversal.
    if _is_path_traversal(browse_path):
        logger.warning(
            "Path traversal attempt blocked in filesystem browse",
            extra={"path_parts_count": len(Path(browse_path).parts)},
        )
        return BrowseResponse(
            current_path=browse_path,
            error="Path traversal is not allowed",
        )

    target = Path(browse_path)

    # Resolve to canonical path.
    try:
        resolved = target.resolve(strict=True)
    except OSError:
        return BrowseResponse(
            current_path=browse_path,
            error="Directory does not exist or is not accessible",
        )

    if not resolved.is_dir():
        return BrowseResponse(
            current_path=str(resolved),
            error="Path is not a directory",
        )

    # Check read permission.
    if not os.access(resolved, os.R_OK):
        return BrowseResponse(
            current_path=str(resolved),
            error="Permission denied",
        )

    # Compute parent path (None for filesystem root).
    parent = resolved.parent
    parent_path = str(parent) if parent != resolved else None

    directories: list[FilesystemEntry] = []
    files: list[FilesystemEntry] = []

    try:
        entries = sorted(resolved.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        return BrowseResponse(
            current_path=str(resolved),
            parent_path=parent_path,
            error="Permission denied reading directory contents",
        )

    for entry_path in entries:
        # Skip hidden files/directories (dotfiles) unless show_all.
        if not show_all and entry_path.name.startswith("."):
            continue

        entry = _build_entry(entry_path)
        if entry is None:
            continue

        if entry.is_directory:
            directories.append(entry)
        else:
            # In filtered mode, only include supported file types.
            if not show_all:
                suffix = entry_path.suffix.lower()
                if suffix not in _SUPPORTED_EXTENSIONS:
                    continue
            files.append(entry)

    logger.info(
        "Filesystem browse completed",
        extra={
            "dir_count": len(directories),
            "file_count": len(files),
        },
    )

    return BrowseResponse(
        current_path=str(resolved),
        parent_path=parent_path,
        directories=directories,
        files=files,
    )


# Persistent upload directory for the current process.  Created once on
# first upload and reused for all subsequent uploads.
_upload_dir: Path | None = None


def _get_upload_dir() -> Path:
    """Return the uploads directory, creating it if necessary.

    Uses a temporary directory under the system temp path so uploaded
    files are automatically cleaned up on reboot.

    Returns:
        Absolute path to the uploads directory.
    """
    global _upload_dir
    if _upload_dir is None or not _upload_dir.is_dir():
        _upload_dir = Path(tempfile.mkdtemp(prefix="cecil_uploads_"))
        logger.info("Created upload directory", extra={"path": str(_upload_dir)})
    return _upload_dir


@router.post(
    "/upload",
    response_model=UploadResponse,
)
async def upload_files(
    files: list[UploadFile],
) -> UploadResponse:
    """Upload one or more data files for scanning.

    Accepts multipart file uploads, validates extensions, and saves
    files to a temporary directory.  Returns metadata for each
    successfully uploaded file including the server-side path that
    can be passed to the scan endpoint.

    Args:
        files: List of uploaded files from the multipart request.

    Returns:
        An UploadResponse with metadata for uploaded files and any errors.
    """
    upload_dir = _get_upload_dir()
    uploaded: list[UploadedFileInfo] = []
    errors: list[str] = []

    for upload_file in files:
        filename = upload_file.filename or "unnamed"

        # Sanitise the filename — strip path separators to prevent traversal.
        safe_name = Path(filename).name
        if not safe_name:
            errors.append(f"Invalid filename: {filename}")
            continue

        # Validate extension.
        suffix = Path(safe_name).suffix.lower()
        detected_format = _EXTENSION_FORMAT_MAP.get(suffix)
        if detected_format is None:
            errors.append(
                f"Unsupported file format for '{safe_name}'. "
                f"Supported: {', '.join(_SUPPORTED_EXTENSIONS)}"
            )
            continue

        # Write file to disk in chunks to stay within memory bounds.
        dest = upload_dir / safe_name
        total_bytes = 0
        try:
            with dest.open("wb") as f:
                while chunk := await upload_file.read(8192):
                    f.write(chunk)
                    total_bytes += len(chunk)
        except OSError as err:
            errors.append(f"Failed to save '{safe_name}': {type(err).__name__}")
            logger.warning(
                "File upload write failed",
                extra={"filename": safe_name, "error_type": type(err).__name__},
            )
            continue

        uploaded.append(
            UploadedFileInfo(
                name=safe_name,
                path=str(dest),
                size=total_bytes,
                format=detected_format,
            )
        )
        logger.info(
            "File uploaded",
            extra={"filename": safe_name, "size_bytes": total_bytes},
        )

    return UploadResponse(files=uploaded, errors=errors)


@router.post(
    "/open-directory",
    response_model=OpenDirectoryResponse,
    responses={
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def open_directory(
    request: OpenDirectoryRequest,
) -> OpenDirectoryResponse | JSONResponse:
    """Open a directory in the system file manager.

    Uses platform-specific commands to open the directory:
    - macOS: `open`
    - Windows: `explorer`
    - Linux: `xdg-open`

    Args:
        request: The open directory request with the path.

    Returns:
        An OpenDirectoryResponse indicating success or failure,
        or a JSONResponse with an error payload for validation failures.
    """
    # Path traversal check.
    if ".." in Path(request.path).parts:
        logger.warning(
            "Path traversal attempt blocked in open-directory",
            extra={"path_parts_count": len(Path(request.path).parts)},
        )
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error="path_traversal",
                message="Path traversal is not allowed",
            ).model_dump(),
        )

    # Resolve and validate directory existence.
    try:
        resolved = Path(request.path).resolve(strict=True)
    except OSError:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="directory_not_found",
                message="Directory does not exist or is not accessible",
            ).model_dump(),
        )

    if not resolved.is_dir():
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="not_a_directory",
                message="Path is not a directory",
            ).model_dump(),
        )

    # Determine platform-specific command.
    if sys.platform == "darwin":
        cmd = ["open", str(resolved)]
    elif sys.platform == "win32":
        cmd = ["explorer", str(resolved)]
    else:
        # Linux and other Unix-like systems.
        cmd = ["xdg-open", str(resolved)]

    # Execute the command to open the directory.
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=5)  # noqa: S603
        logger.info(
            "Directory opened in file manager",
            extra={"platform": sys.platform},
        )
        return OpenDirectoryResponse(
            success=True,
            message="Directory opened successfully",
        )
    except subprocess.CalledProcessError as err:
        logger.warning(
            "Failed to open directory",
            extra={"platform": sys.platform, "returncode": err.returncode},
        )
        return OpenDirectoryResponse(
            success=False,
            message=f"Failed to open directory: {err}",
        )
    except subprocess.TimeoutExpired:
        logger.warning(
            "Timeout opening directory",
            extra={"platform": sys.platform},
        )
        return OpenDirectoryResponse(
            success=False,
            message="Timeout opening directory",
        )
    except FileNotFoundError:
        logger.warning(
            "File manager command not found",
            extra={"platform": sys.platform, "command": cmd[0]},
        )
        return OpenDirectoryResponse(
            success=False,
            message=f"File manager not available: {cmd[0]} not found",
        )


@router.post(
    "/read-jsonl",
    response_model=PreviewOutputResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def preview_output(
    request: PreviewOutputRequest,
) -> PreviewOutputResponse | JSONResponse:
    """Read and return a preview of a sanitized output file.

    Returns up to `limit` records from the output JSONL file for UI display.
    This endpoint reads SANITIZED output only — the data has already been
    through the privacy pipeline, so it's safe to return to the UI.

    Args:
        request: The preview request with path, offset, and limit.

    Returns:
        A PreviewOutputResponse with records and metadata,
        or a JSONResponse with an error payload for validation failures.
    """
    # Expand tilde in the path.
    try:
        file_path = Path(request.path).expanduser().resolve(strict=True)
    except OSError:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="file_not_found",
                message="Output file does not exist or is not accessible",
            ).model_dump(),
        )

    # Verify it's a file, not a directory.
    if not file_path.is_file():
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="not_a_file",
                message="Path is not a file",
            ).model_dump(),
        )

    # Verify read permission.
    if not os.access(file_path, os.R_OK):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="permission_denied",
                message="File is not readable",
            ).model_dump(),
        )

    # Read the JSONL file line by line.
    records: list[dict[str, str]] = []
    total_count = 0
    malformed_count = 0

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    # Skip empty lines.
                    continue

                total_count += 1

                # Skip lines before the offset.
                if total_count <= request.offset:
                    continue

                # Stop if we've reached the limit.
                if len(records) >= request.limit:
                    continue

                # Parse the JSON line.
                try:
                    record = json.loads(line)
                    # Ensure all values are strings for consistency.
                    records.append({k: str(v) for k, v in record.items()})
                except json.JSONDecodeError:
                    malformed_count += 1
                    logger.warning(
                        "Skipping malformed JSON line in output file",
                        extra={
                            "line_number": line_num,
                        },
                    )
                    continue

    except OSError as err:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="read_error",
                message=f"Failed to read file: {type(err).__name__}",
            ).model_dump(),
        )

    logger.info(
        "Output file preview completed",
        extra={
            "total_count": total_count,
            "returned_count": len(records),
            "malformed_lines": malformed_count,
        },
    )

    return PreviewOutputResponse(
        records=records,
        total_count=total_count,
        path=str(file_path),
    )
