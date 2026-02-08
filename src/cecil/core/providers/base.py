"""Base data provider interface.

Defines the abstract contract that all data ingestion providers must
implement to participate in the Safe-Pipe streaming pipeline.
"""

from __future__ import annotations

import abc
import logging
from collections.abc import Generator
from typing import Any


logger = logging.getLogger(__name__)


class BaseDataProvider(abc.ABC):
    """Abstract base for all data ingestion providers.

    Subclasses must implement ``connect``, ``stream_records``, ``close``,
    and ``fetch_metadata``.  The ``stream_records`` method must yield
    records as dictionaries to maintain the 50 MB memory bound.

    Supports the context-manager protocol so providers can be used with
    ``with`` statements for automatic resource cleanup.
    """

    @abc.abstractmethod
    def connect(self) -> None:
        """Establish a connection to the data source.

        Raises:
            ProviderConnectionError: If the connection cannot be made.
        """

    @abc.abstractmethod
    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        """Yield data records one at a time from the source.

        Implementations must **not** buffer the entire dataset in memory.
        Each yielded record should be a flat or nested dictionary.

        Yields:
            A single data record as a dictionary.

        Raises:
            ProviderReadError: If reading from the source fails.
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Release resources and close the connection."""

    @abc.abstractmethod
    def fetch_metadata(self) -> dict[str, Any]:
        """Return non-sensitive metadata about the data source.

        Metadata may include record count estimates, schema info, and
        source identifiers.  Must never include PII.

        Returns:
            A dictionary of metadata key-value pairs.
        """

    # ── Context manager protocol ───────────────────────────────────────

    def __enter__(self) -> BaseDataProvider:
        """Connect to the data source on entering the context."""
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the connection on exiting the context."""
        self.close()
