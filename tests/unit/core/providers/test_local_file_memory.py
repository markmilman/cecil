"""Memory bound tests for LocalFileProvider.

Verifies that streaming 10MB+ JSONL and CSV files through
LocalFileProvider stays under the Safe-Pipe 50MB memory ceiling,
and that the generator yields records lazily without accumulating
them in memory.
"""

from __future__ import annotations

import os
import tracemalloc
from pathlib import Path

import pytest

from cecil.core.providers.local_file import LocalFileProvider
from tests.fixtures.pii_samples import (
    generate_sample_csv,
    generate_sample_jsonl,
)


MEMORY_CEILING_BYTES = 50 * 1024 * 1024  # 50 MB
TARGET_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _generate_large_jsonl(path: Path, target_bytes: int = TARGET_FILE_SIZE_BYTES) -> int:
    """Generate a JSONL file of at least ``target_bytes`` size.

    Writes records in batches using ``generate_sample_jsonl`` until the
    file exceeds the target size.  Returns the total number of records
    written.

    Args:
        path: Filesystem path for the output JSONL file.
        target_bytes: Minimum file size in bytes to produce.

    Returns:
        The number of records written to the file.
    """
    # Each record from generate_sample_jsonl is roughly 500-700 bytes.
    # Write a batch size that lets us overshoot in a few iterations.
    batch_size = 500
    total_records = 0

    # Write in batches until file exceeds target size.
    # Use append mode after the first write.
    while True:
        if total_records == 0:
            generate_sample_jsonl(str(path), count=batch_size)
        else:
            # Append more records by generating to a temp file and
            # appending its contents.
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".jsonl",
                delete=False,
                dir=str(path.parent),
            ) as tmp:
                tmp_name = tmp.name
            generate_sample_jsonl(tmp_name, count=batch_size)
            with (
                open(tmp_name, encoding="utf-8") as src,
                open(
                    path,
                    "a",
                    encoding="utf-8",
                ) as dst,
            ):
                for line in src:
                    dst.write(line)
            os.unlink(tmp_name)

        total_records += batch_size

        file_size = path.stat().st_size
        if file_size >= target_bytes:
            break

    return total_records


def _generate_large_csv(path: Path, target_bytes: int = TARGET_FILE_SIZE_BYTES) -> int:
    """Generate a CSV file of at least ``target_bytes`` size.

    Writes records using ``generate_sample_csv`` with enough rows to
    exceed the target file size.

    Args:
        path: Filesystem path for the output CSV file.
        target_bytes: Minimum file size in bytes to produce.

    Returns:
        The number of data rows written (excluding the header).
    """
    # A single CSV row is roughly 80-120 bytes.  Estimate the count
    # needed to exceed target_bytes, then add a margin.
    estimated_row_size = 90
    count = (target_bytes // estimated_row_size) + 1000
    generate_sample_csv(str(path), count=count)

    # If we undershot, keep growing until we pass the target.
    while path.stat().st_size < target_bytes:
        count += 5000
        generate_sample_csv(str(path), count=count)

    return count


class TestLocalFileProviderMemoryBound:
    """Verify LocalFileProvider stays under 50MB peak memory with large files."""

    @pytest.mark.slow
    def test_jsonl_10mb_stays_under_50mb_peak(self, tmp_path: Path) -> None:
        """Generate 10MB+ JSONL, stream through provider, verify peak < 50MB."""
        path = tmp_path / "large.jsonl"
        total_records = _generate_large_jsonl(path)

        assert path.stat().st_size >= TARGET_FILE_SIZE_BYTES, (
            f"Generated JSONL is only {path.stat().st_size} bytes, "
            f"expected >= {TARGET_FILE_SIZE_BYTES}"
        )

        tracemalloc.start()

        provider = LocalFileProvider(file_path=path)
        provider.connect()
        count = 0
        for _record in provider.stream_records():
            count += 1
        provider.close()

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert count == total_records, f"Expected {total_records} records, got {count}"
        assert peak < MEMORY_CEILING_BYTES, (
            f"Peak memory {peak / 1024 / 1024:.1f} MB exceeds 50 MB bound"
        )

    @pytest.mark.slow
    def test_csv_10mb_stays_under_50mb_peak(self, tmp_path: Path) -> None:
        """Generate 10MB+ CSV, stream through provider, verify peak < 50MB."""
        path = tmp_path / "large.csv"
        total_records = _generate_large_csv(path)

        assert path.stat().st_size >= TARGET_FILE_SIZE_BYTES, (
            f"Generated CSV is only {path.stat().st_size} bytes, "
            f"expected >= {TARGET_FILE_SIZE_BYTES}"
        )

        tracemalloc.start()

        provider = LocalFileProvider(file_path=path)
        provider.connect()
        count = 0
        for _record in provider.stream_records():
            count += 1
        provider.close()

        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert count == total_records, f"Expected {total_records} records, got {count}"
        assert peak < MEMORY_CEILING_BYTES, (
            f"Peak memory {peak / 1024 / 1024:.1f} MB exceeds 50 MB bound"
        )

    def test_generator_does_not_accumulate_records(self, tmp_path: Path) -> None:
        """Verify streaming yields lazily (not collecting into list internally).

        Checks that memory does not grow linearly with the number of
        records consumed from the generator.  We measure the memory
        after consuming a small subset of records vs. all records and
        verify no large accumulation.
        """
        path = tmp_path / "medium.jsonl"
        record_count = 2000
        generate_sample_jsonl(str(path), count=record_count)

        tracemalloc.start()

        provider = LocalFileProvider(file_path=path)
        provider.connect()
        gen = provider.stream_records()

        # Consume first 100 records
        for _ in range(100):
            next(gen)
        _, peak_early = tracemalloc.get_traced_memory()

        # Consume remaining records
        count = 100
        for _record in gen:
            count += 1
        _, peak_final = tracemalloc.get_traced_memory()

        provider.close()
        tracemalloc.stop()

        assert count == record_count, f"Expected {record_count} records, got {count}"

        # Memory should not have grown by more than 5MB between the
        # two checkpoints -- if the generator were accumulating all
        # records, peak_final would be significantly larger.
        growth = peak_final - peak_early
        max_allowed_growth = 5 * 1024 * 1024  # 5 MB
        assert growth < max_allowed_growth, (
            f"Memory grew by {growth / 1024 / 1024:.1f} MB between early "
            f"and final reads, suggesting records are being accumulated"
        )
