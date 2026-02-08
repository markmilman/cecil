"""Local file data provider.

Reads structured data from local files (JSONL, CSV, Parquet) and yields
records one at a time through a memory-efficient generator.

Supported formats:

- **JSONL**: Each line is a JSON object yielding ``dict[str, Any]``.
- **CSV**: Uses ``csv.DictReader`` for streaming.  Note that all CSV
  values are strings (``dict[str, str]``) because ``csv.DictReader``
  does not perform type coercion.  Callers that need typed values
  should cast after receiving records.  Custom delimiter and quoting
  options can be passed to the constructor.
- **Parquet**: Uses PyArrow (optional dependency) for row-group-based
  streaming.  Values are converted to native Python types via
  ``.as_py()``.

Malformed records are skipped rather than raising exceptions, and
optionally logged to a quarantine file for later inspection.
"""

from __future__ import annotations

import contextlib
import csv
import datetime
import json
import logging
import os
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import IO, Any, Literal

from cecil.core.providers.base import BaseDataProvider
from cecil.utils.errors import (
    ProviderConnectionError,
    ProviderDependencyError,
    ProviderReadError,
)


logger = logging.getLogger(__name__)

# Mapping of file extensions to canonical format identifiers.
_EXTENSION_FORMAT_MAP: dict[str, str] = {
    ".jsonl": "jsonl",
    ".csv": "csv",
    ".parquet": "parquet",
}

# Valid quoting constants for csv module.
_QuotingType = Literal[0, 1, 2, 3]

# I/O buffer size for open() calls (8 KB).
_IO_BUFFER_SIZE = 8192

# Parquet magic bytes at the start of a valid file.
_PARQUET_MAGIC = b"PAR1"


class LocalFileProvider(BaseDataProvider):
    """Provider that streams records from a local file.

    Supports automatic format detection from the file extension, or an
    explicit format_hint override.  Currently JSONL and CSV files are
    handled.  Parquet files are also supported when PyArrow is installed.

    Malformed records encountered during streaming are skipped (not
    raised) and optionally written to a quarantine log file.

    Args:
        file_path: Path to the local file to read.
        format_hint: Override format detection (e.g. "jsonl").
            When None, the format is inferred from the file extension.
        encoding: Text encoding for the file.  Defaults to "utf-8".
        delimiter: Column delimiter for CSV files.  Defaults to ",".
        quoting: Quoting strategy for CSV files.  Defaults to
            ``csv.QUOTE_MINIMAL``.
        quarantine_path: Optional path for writing quarantine log entries.
            When None, quarantine logging is disabled (malformed records
            are still skipped with a warning).
    """

    def __init__(
        self,
        file_path: str | Path,
        format_hint: str | None = None,
        encoding: str = "utf-8",
        delimiter: str = ",",
        quoting: _QuotingType = csv.QUOTE_MINIMAL,
        quarantine_path: Path | None = None,
    ) -> None:
        self._file_path = Path(file_path)
        self._format_hint = format_hint
        self._encoding = encoding
        self._delimiter = delimiter
        self._quoting: _QuotingType = quoting
        self._quarantine_path = quarantine_path
        self._quarantine_handle: IO[str] | None = None
        self._file_handle: Any | None = None
        self._record_count: int = 0
        self._records_quarantined: int = 0
        self._format: str = self._detect_format()

    # -- Public interface ---------------------------------------------------

    def connect(self) -> None:
        """Verify the file exists, open it, and validate the format.

        Checks file existence, readability, non-zero size, and that
        the content matches the expected format by inspecting the first
        bytes or lines of the file.

        Raises:
            ProviderConnectionError: If the file does not exist, is not
                readable, is empty, or the content does not match the
                expected format.
        """
        if not self._file_path.exists():
            raise ProviderConnectionError(f"File not found: {self._file_path}")
        if not self._file_path.is_file():
            raise ProviderConnectionError(f"Path is not a regular file: {self._file_path}")
        if not os.access(self._file_path, os.R_OK):
            raise ProviderConnectionError(f"File is not readable: {self._file_path}")

        # Reject zero-byte files early.
        try:
            file_size = self._file_path.stat().st_size
        except OSError as err:
            raise ProviderConnectionError(
                f"Cannot stat file: {self._file_path}",
            ) from err
        if file_size == 0:
            raise ProviderConnectionError(f"File is empty (zero bytes): {self._file_path}")

        # Validate content matches the expected format.
        self._validate_format_content()

        # Parquet files are opened by PyArrow directly, not by us.
        if self._format != "parquet":
            try:
                self._file_handle = open(  # noqa: SIM115
                    self._file_path,
                    encoding=self._encoding,
                    buffering=_IO_BUFFER_SIZE,
                )
            except OSError as err:
                raise ProviderConnectionError(
                    f"Cannot open file: {self._file_path}",
                ) from err

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
        For CSV files each row is yielded as a ``dict[str, str]``.
        For Parquet files, row groups are read incrementally and
        individual rows are yielded as ``dict[str, Any]``.
        Blank lines are silently skipped in text-based formats.
        Malformed records are skipped and optionally quarantined.

        Yields:
            A single data record as a dictionary.

        Raises:
            ProviderReadError: If the file handle is not open.
            ProviderDependencyError: If pyarrow is not installed for
                Parquet files.
            NotImplementedError: If the file format is not yet supported.
        """
        if self._format == "jsonl":
            yield from self._stream_jsonl()
        elif self._format == "csv":
            yield from self._stream_csv()
        elif self._format == "parquet":
            yield from self._stream_parquet()
        else:
            raise NotImplementedError(f"Format not yet supported: {self._format}")

    def close(self) -> None:
        """Close the file handle and release resources.

        Safe to call multiple times.  Also closes the quarantine log
        handle if it was opened.
        """
        if self._file_handle is not None:
            with contextlib.suppress(OSError):
                self._file_handle.close()
            self._file_handle = None
        if self._quarantine_handle is not None:
            with contextlib.suppress(OSError):
                self._quarantine_handle.close()
            self._quarantine_handle = None
        logger.info(
            "LocalFileProvider closed",
            extra={"path": str(self._file_path)},
        )

    def fetch_metadata(self) -> dict[str, Any]:
        """Return non-sensitive metadata about the file.

        Returns:
            A dictionary with provider key, file path, size, format,
            the number of records streamed so far, and the number of
            records quarantined.
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
            "records_quarantined": self._records_quarantined,
        }

    # -- Properties ---------------------------------------------------------

    @property
    def file_path(self) -> Path:
        """The resolved path to the data file."""
        return self._file_path

    @property
    def format(self) -> str:
        """The detected or overridden format identifier."""
        return self._format

    # -- Private helpers ----------------------------------------------------

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

    def _validate_format_content(self) -> None:
        """Validate that the file content matches the expected format.

        Peeks at the first bytes or lines of the file and checks for
        format-specific markers.  Uses separate file handles for
        validation so the main file handle is not affected.

        Raises:
            ProviderConnectionError: If the content does not match the
                expected format.
        """
        if self._format == "jsonl":
            self._validate_jsonl_content()
        elif self._format == "csv":
            self._validate_csv_content()
        elif self._format == "parquet":
            self._validate_parquet_content()

    def _validate_jsonl_content(self) -> None:
        """Validate that the file contains parseable JSONL content.

        Reads through lines until a non-blank line is found, then
        attempts to parse it as JSON.

        Raises:
            ProviderConnectionError: If the first non-blank line is not
                valid JSON.
        """
        try:
            with open(
                self._file_path,
                encoding=self._encoding,
                buffering=_IO_BUFFER_SIZE,
            ) as fh:
                for line in fh:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        json.loads(stripped)
                    except json.JSONDecodeError as err:
                        raise ProviderConnectionError(
                            "File content does not appear to be valid JSONL",
                        ) from err
                    return
        except ProviderConnectionError:
            raise
        except OSError as err:
            raise ProviderConnectionError(
                f"Cannot read file for validation: {self._file_path}",
            ) from err

    def _validate_csv_content(self) -> None:
        """Validate that the file contains a parseable CSV header.

        Reads the first line and checks that it yields at least one
        non-empty field when parsed as CSV.  Also rejects binary
        content (null bytes).

        Raises:
            ProviderConnectionError: If the first line cannot be parsed
                as a valid CSV header.
        """
        try:
            with open(
                self._file_path,
                encoding=self._encoding,
                buffering=_IO_BUFFER_SIZE,
            ) as fh:
                try:
                    first_line = fh.readline()
                except UnicodeDecodeError as err:
                    raise ProviderConnectionError(
                        "File content does not appear to be valid CSV",
                    ) from err
                if not first_line.strip():
                    raise ProviderConnectionError(
                        "File content does not appear to be valid CSV",
                    )
                # Check for binary content (null bytes).
                if "\x00" in first_line:
                    raise ProviderConnectionError(
                        "File content does not appear to be valid CSV",
                    )
                try:
                    reader = csv.reader([first_line], delimiter=self._delimiter)
                    fields = next(reader)
                except (csv.Error, StopIteration) as err:
                    raise ProviderConnectionError(
                        "File content does not appear to be valid CSV",
                    ) from err
                # A single empty field means the header is effectively empty.
                if len(fields) == 1 and fields[0].strip() == "":
                    raise ProviderConnectionError(
                        "File content does not appear to be valid CSV",
                    )
        except ProviderConnectionError:
            raise
        except OSError as err:
            raise ProviderConnectionError(
                f"Cannot read file for validation: {self._file_path}",
            ) from err

    def _validate_parquet_content(self) -> None:
        """Validate that the file starts with the PAR1 magic bytes.

        Reads the first 4 bytes in binary mode and checks for the
        Parquet magic signature.

        Raises:
            ProviderConnectionError: If the PAR1 magic bytes are missing.
        """
        try:
            with open(self._file_path, "rb") as fh:
                magic = fh.read(4)
        except OSError as err:
            raise ProviderConnectionError(
                f"Cannot read file for validation: {self._file_path}",
            ) from err
        if magic != _PARQUET_MAGIC:
            raise ProviderConnectionError(
                "File content does not appear to be valid Parquet (missing PAR1 magic bytes)",
            )

    def _write_quarantine_entry(
        self,
        line_number: int,
        error_type: str,
    ) -> None:
        """Write a quarantine log entry for a malformed record.

        Opens the quarantine file lazily on first call.  Each entry is
        a single JSON line containing the line number, error type,
        timestamp, and source file path -- never raw data or PII.

        Args:
            line_number: The 1-based line number of the malformed record.
            error_type: A short description of the error (e.g.
                "JSONDecodeError", "csv.Error").
        """
        if self._quarantine_path is None:
            return

        if self._quarantine_handle is None:
            self._quarantine_handle = open(  # noqa: SIM115
                self._quarantine_path,
                "a",
                encoding="utf-8",
            )

        entry = {
            "line_number": line_number,
            "error_type": error_type,
            "timestamp": datetime.datetime.now(tz=datetime.UTC).isoformat(),
            "source_file": str(self._file_path),
        }
        self._quarantine_handle.write(json.dumps(entry) + "\n")
        self._quarantine_handle.flush()

    def _stream_jsonl(self) -> Generator[dict[str, Any], None, None]:
        """Stream records from a JSONL file.

        Malformed lines are skipped with a warning and optionally
        written to the quarantine log.

        Yields:
            Parsed JSON objects one at a time.

        Raises:
            ProviderReadError: If the file handle is not open.
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
            except json.JSONDecodeError:
                logger.warning(
                    "Skipping malformed record",
                    extra={
                        "line_number": line_number,
                        "error_type": "JSONDecodeError",
                    },
                )
                self._records_quarantined += 1
                self._write_quarantine_entry(line_number, "JSONDecodeError")
                continue
            self._record_count += 1
            yield record

        logger.info(
            "JSONL stream complete",
            extra={
                "path": str(self._file_path),
                "records_yielded": self._record_count,
                "records_quarantined": self._records_quarantined,
            },
        )

    def _stream_csv(self) -> Generator[dict[str, Any], None, None]:
        """Stream records from a CSV file.

        Uses ``csv.DictReader`` so each row is yielded as a
        ``dict[str, str]`` (a subtype of ``dict[str, Any]``).
        Empty rows (where all values are ``None`` or empty strings)
        are silently skipped.  Malformed rows are skipped with a
        warning and optionally written to the quarantine log.

        Yields:
            A single CSV row as a dictionary mapping column names to
            string values.

        Raises:
            ProviderReadError: If the file handle is not open.
        """
        if self._file_handle is None:
            raise ProviderReadError("File handle is not open. Call connect() first.")

        self._record_count = 0
        # Cast file handle from Any to Iterable[str] for mypy overload
        # resolution; at runtime _file_handle is always a text-mode file.
        handle: Iterable[str] = self._file_handle
        reader = csv.DictReader(
            handle,
            delimiter=self._delimiter,
            quoting=self._quoting,
        )
        line_number = 1  # Header is line 1
        for row in reader:
            line_number += 1
            try:
                # Skip empty rows: all values are None or whitespace-only.
                # Note: DictReader may store excess fields as a list
                # under restkey, so we must handle non-string values.
                if all(
                    v is None or (isinstance(v, str) and v.strip() == "") for v in row.values()
                ):
                    continue
                self._record_count += 1
                yield dict(row)
            except (csv.Error, AttributeError):
                logger.warning(
                    "Skipping malformed record",
                    extra={
                        "line_number": line_number,
                        "error_type": "csv.Error",
                    },
                )
                self._records_quarantined += 1
                self._write_quarantine_entry(line_number, "csv.Error")
                continue

        logger.info(
            "CSV stream complete",
            extra={
                "path": str(self._file_path),
                "records_yielded": self._record_count,
                "records_quarantined": self._records_quarantined,
            },
        )

    def _stream_parquet(self) -> Generator[dict[str, Any], None, None]:
        """Stream records from a Parquet file using PyArrow.

        Reads row groups incrementally via ``pyarrow.parquet.ParquetFile``
        to keep memory usage bounded.  Each row is converted to a Python
        dictionary with native Python types (via ``.as_py()``).

        Yields:
            A single row as a dictionary with Python-native values.

        Raises:
            ProviderDependencyError: If ``pyarrow`` is not installed.
            ProviderReadError: If the Parquet file cannot be read.
        """
        try:
            import pyarrow.parquet as pq  # type: ignore  # optional dep: untyped or absent
        except ImportError as err:
            raise ProviderDependencyError(
                "Parquet support requires pyarrow. Install with: pip install pyarrow",
            ) from err

        try:
            pf = pq.ParquetFile(self._file_path)
        except Exception as err:
            raise ProviderReadError(
                f"Cannot read Parquet file: {self._file_path}",
            ) from err

        self._record_count = 0
        column_names: list[str] = pf.schema_arrow.names

        for row_group_idx in range(pf.metadata.num_row_groups):
            table = pf.read_row_group(row_group_idx)
            for batch in table.to_batches():
                # Convert columnar batch to row-wise dicts efficiently.
                columns: dict[str, Any] = {name: batch.column(name) for name in column_names}
                for row_idx in range(batch.num_rows):
                    record: dict[str, Any] = {
                        name: columns[name][row_idx].as_py() for name in column_names
                    }
                    self._record_count += 1
                    yield record

        logger.info(
            "Parquet stream complete",
            extra={
                "path": str(self._file_path),
                "records_yielded": self._record_count,
            },
        )
