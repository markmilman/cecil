"""Mock data provider for testing.

Provides a concrete ``BaseDataProvider`` implementation that yields
pre-loaded records from memory, enabling unit and integration tests
without external dependencies or real data sources.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from cecil.core.providers.base import BaseDataProvider


logger = logging.getLogger(__name__)


class MockDataProvider(BaseDataProvider):
    """In-memory provider that yields pre-loaded records.

    Useful for testing the sanitization pipeline without connecting to
    a real data source.

    Args:
        records: Sequence of dictionaries to yield from ``stream_records``.
        metadata: Optional metadata dict returned by ``fetch_metadata``.
    """

    def __init__(
        self,
        records: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._records = records or []
        self._metadata = metadata or {}
        self._connected = False

    @property
    def connected(self) -> bool:
        """Whether the provider is currently connected."""
        return self._connected

    def connect(self) -> None:
        """Mark the provider as connected."""
        logger.info("MockDataProvider connected", extra={"record_count": len(self._records)})
        self._connected = True

    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        """Yield pre-loaded records one at a time.

        Yields:
            A single data record as a dictionary.
        """
        logger.info(
            "Starting mock record stream",
            extra={"record_count": len(self._records)},
        )
        count = 0
        for record in self._records:
            count += 1
            yield record
        logger.info("Mock record stream complete", extra={"records_yielded": count})

    def close(self) -> None:
        """Mark the provider as disconnected."""
        self._connected = False
        logger.info("MockDataProvider closed")

    def fetch_metadata(self) -> dict[str, Any]:
        """Return the pre-configured metadata dictionary.

        Returns:
            A dictionary of metadata key-value pairs.
        """
        return {
            "provider": "mock",
            "record_count": len(self._records),
            **self._metadata,
        }
