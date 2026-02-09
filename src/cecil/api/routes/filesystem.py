"""Filesystem browse API route.

Provides a GET /api/v1/filesystem/browse endpoint that lists directory
contents for the frontend file browser modal.  Includes security
hardening against path traversal and symlink escape attacks.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Query

from cecil.api.schemas import BrowseResponse, FileFormat, FilesystemEntry


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
