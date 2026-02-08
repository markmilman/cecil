"""Local file data provider.

Reads structured data from local files (JSONL, CSV, Parquet) and yields
records one at a time through a memory-efficient generator.  Only JSONL
is supported in this initial implementation; CSV and Parquet handlers
will be added in subsequent sub-issues.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

from cecil.core.providers.base import BaseDataProvider
from cecil.utils.errors import ProviderConnectionError, ProviderReadError


logger = logging.getLogger(__name__)

# Mapping of file extensions to canonical format identifiers.
_EXTENSION_FORMAT_MAP: dict[str, str] = {
    ".jsonl": "jsonl",
    ".csv": "csv",
    ".parquet": "parquet",
}

# I/O buffer size for open() calls (8 KB).
_IO_BUFFER_SIZE = 8192


class LocalFileProvider(BaseDataProvider):
    """Provider that streams records from a local file.

    Supports automatic format detection from the file extension, or an
    explicit format_hint override.  Currently only JSONL files are
    handled; CSV and Parquet support will be added later.

    Args:
        file_path: Path to the local file to read.
        format_hint: Override format detection (e.g. "jsonl").
            When None, the format is inferred from the file extension.
        encoding: Text encoding for the file.  Defaults to "utf-8".
    """

    def __init__(
        self,
        file_path: str | Path,
        format_hint: str | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self._file_path = Path(file_path)
        self._format_hint = format_hint
        self._encoding = encoding
        self._file_handle: Any | None = None
        self._record_count: int = 0
        self._format: str = self._detect_format()

    # ── Public interface ───────────────────────────────────────────────

    def connect(self) -> None:
        """Verify the file exists and open it for reading.

        Raises:
            ProviderConnectionError: If the file does not exist or is not
                readable.
        """
        if not self._file_path.exists():
            raise ProviderConnectionError(f"File not found: {self._file_path}")
        if not self._file_path.is_file():
            raise ProviderConnectionError(f"Path is not a regular file: {self._file_path}")
        if not os.access(self._file_path, os.R_OK):
            raise ProviderConnectionError(f"File is not readable: {self._file_path}")

        try:
            self._file_handle = open(  # noqa: SIM115
                self._file_path,
                encoding=self._encoding,
                buffering=_IO_BUFFER_SIZE,
            )
        except OSError as err:
            raise ProviderConnectionError(f"Cannot open file: {self._file_path}") from err

        logger.info(
            "LocalFileProvider connected",
            extra={
                "path": str(self._file_path),
                "format": self._format,
            },
        )

    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        """Yield records one at a time from the file.

        For JSONL files each line is parsed as a separate JSON object.
        Blank lines are silently skipped.

        Yields:
            A single data record as a dictionary.

        Raises:
            ProviderReadError: If a line cannot be parsed as JSON.
            NotImplementedError: If the file format is not yet supported.
        """
        if self._format != "jsonl":
            raise NotImplementedError(f"Format not yet supported: {self._format}")
        yield from self._stream_jsonl()

    def close(self) -> None:
        """Close the file handle and release resources.

        Safe to call multiple times.
        """
        if self._file_handle is not None:
            with contextlib.suppress(OSError):
                self._file_handle.close()
            self._file_handle = None
        logger.info(
            "LocalFileProvider closed",
            extra={"path": str(self._file_path)},
        )

    def fetch_metadata(self) -> dict[str, Any]:
        """Return non-sensitive metadata about the file.

        Returns:
            A dictionary with provider key, file path, size, format,
            and the number of records streamed so far.
        """
        size: int | None = None
        with contextlib.suppress(OSError):
            size = self._file_path.stat().st_size

        return {
            "provider": "local_file",
            "file_path": str(self._file_path),
            "file_size_bytes": size,
            "format": self._format,
            "record_count": self._record_count,
        }

    # ── Properties ─────────────────────────────────────────────────────

    @property
    def file_path(self) -> Path:
        """The resolved path to the data file."""
        return self._file_path

    @property
    def format(self) -> str:
        """The detected or overridden format identifier."""
        return self._format

    # ── Private helpers ────────────────────────────────────────────────

    def _detect_format(self) -> str:
        """Determine file format from hint or extension.

        Returns:
            A canonical format string (e.g. "jsonl").

        Raises:
            ProviderConnectionError: If the format cannot be determined.
        """
        if self._format_hint is not None:
            return self._format_hint.lower()

        suffix = self._file_path.suffix.lower()
        fmt = _EXTENSION_FORMAT_MAP.get(suffix)
        if fmt is None:
            raise ProviderConnectionError(
                f"Cannot detect format for extension '{suffix}'. Provide a format_hint."
            )
        return fmt

    def _stream_jsonl(self) -> Generator[dict[str, Any], None, None]:
        """Stream records from a JSONL file.

        Yields:
            Parsed JSON objects one at a time.

        Raises:
            ProviderReadError: If a non-blank line is not valid JSON.
        """
        if self._file_handle is None:
            raise ProviderReadError("File handle is not open. Call connect() first.")

        self._record_count = 0
        line_number = 0
        for raw_line in self._file_handle:
            line_number += 1
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                record: dict[str, Any] = json.loads(stripped)
            except json.JSONDecodeError as err:
                raise ProviderReadError(
                    f"Invalid JSON on line {line_number} of {self._file_path}"
                ) from err
            self._record_count += 1
            yield record

        logger.info(
            "JSONL stream complete",
            extra={
                "path": str(self._file_path),
                "records_yielded": self._record_count,
            },
        )
