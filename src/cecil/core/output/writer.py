"""Streaming JSONL output writer.

Writes sanitized records as JSON Lines to a file, flushing each
record immediately to respect the 50 MB memory ceiling.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class JsonlWriter:
    """Streaming JSONL output writer.

    Writes sanitized records as JSON Lines to a file, flushing
    each record immediately to respect the 50MB memory ceiling.
    Supports the context manager protocol.

    Args:
        output_path: The file path to write JSONL output to.
            Parent directories are created if they don't exist.

    Attributes:
        output_path: The resolved output file path.
        records_written: Number of records successfully written.
    """

    def __init__(self, output_path: Path) -> None:
        self.output_path: Path = output_path
        self.records_written: int = 0
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(output_path, "w", encoding="utf-8")  # noqa: SIM115

    def write_record(self, record: dict[str, Any]) -> None:
        """Write a single record as a JSON line.

        Serializes the record to JSON, writes it as a single line,
        and flushes the buffer immediately.

        Args:
            record: The dictionary record to write.
        """
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._file.flush()
        self.records_written += 1

    def close(self) -> None:
        """Close the underlying file handle."""
        if self._file and not self._file.closed:
            self._file.close()

    def __enter__(self) -> JsonlWriter:
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the context manager, closing the file."""
        self.close()
