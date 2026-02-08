"""Memory bounds tests for the streaming generator.

Verifies that iterating over a large dataset via MockDataProvider stays
under the 50 MB resident-memory ceiling required by the Safe-Pipe
architecture.
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Generator
from typing import Any

from cecil.core.providers.base import BaseDataProvider


class _LargeStreamProvider(BaseDataProvider):
    """Provider that generates records on-the-fly without buffering.

    Each record is ~1 KB of data.  Generating *num_records* records
    simulates a dataset of roughly ``num_records`` KB.
    """

    def __init__(self, num_records: int = 10_000) -> None:
        self._num_records = num_records

    def connect(self) -> None: ...

    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        for i in range(self._num_records):
            # ~1 KB per record (padding with character data)
            yield {
                "id": str(i),
                "payload": "x" * 1000,
                "model": "gpt-4",
                "tokens": "150",
            }

    def close(self) -> None: ...

    def fetch_metadata(self) -> dict[str, Any]:
        return {"provider": "large_stream", "num_records": self._num_records}


MEMORY_CEILING_BYTES = 50 * 1024 * 1024  # 50 MB


def test_stream_records_with_10mb_input_stays_under_memory_bound():
    """Processing ~10 MB of generated records must stay under 50 MB peak."""
    # ~10,000 records * ~1 KB each ≈ 10 MB of data generated
    provider = _LargeStreamProvider(num_records=10_000)

    tracemalloc.start()

    provider.connect()
    count = 0
    for _record in provider.stream_records():
        count += 1
    provider.close()

    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert count == 10_000
    assert (
        peak < MEMORY_CEILING_BYTES
    ), f"Peak memory {peak / 1024 / 1024:.1f} MB exceeds 50 MB bound"


def test_stream_records_with_50mb_input_stays_under_memory_bound():
    """Processing ~50 MB of generated records must stay under 50 MB peak.

    Because the generator yields one record at a time, peak memory
    should remain well below the total data volume.
    """
    # ~50,000 records * ~1 KB each ≈ 50 MB of data generated
    provider = _LargeStreamProvider(num_records=50_000)

    tracemalloc.start()

    provider.connect()
    count = 0
    for _record in provider.stream_records():
        count += 1
    provider.close()

    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert count == 50_000
    assert (
        peak < MEMORY_CEILING_BYTES
    ), f"Peak memory {peak / 1024 / 1024:.1f} MB exceeds 50 MB bound"
