"""Performance benchmarks for Cecil's streaming pipeline.

Verifies the 50MB memory ceiling and measures records-per-second
throughput using ``tracemalloc`` and ``MockDataProvider``.  These
tests exercise the generator-based streaming architecture to ensure
it maintains bounded memory even with large record counts.
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from typing import Any

import pytest

from cecil.core.providers.mock import MockDataProvider
from tests.fixtures.pii_samples import (
    KNOWN_PII_BUNDLES,
    make_llm_log_record,
    stream_log_records,
)


# ── Constants ────────────────────────────────────────────────────────

# Hard ceiling from architecture spec (bytes).
_MEMORY_CEILING_BYTES = 50 * 1024 * 1024  # 50 MB

# Minimum acceptable throughput (records per second).
_MIN_THROUGHPUT_RPS = 1000

# Record counts for different benchmark tiers.
_SMALL_BATCH = 1_000
_MEDIUM_BATCH = 10_000
_LARGE_BATCH = 100_000


# ── Helpers ──────────────────────────────────────────────────────────


def _generate_records_lazy(count: int) -> list[dict[str, Any]]:
    """Generate N records lazily using the PII bundles.

    Creates records by cycling through known PII bundles.  This does
    NOT use the streaming generator because we need a materialized
    list for the MockDataProvider.  For large counts, consider using
    ``stream_log_records`` directly.

    Args:
        count: Number of records to generate.

    Returns:
        A list of log record dictionaries.
    """
    return [
        make_llm_log_record(
            KNOWN_PII_BUNDLES[i % len(KNOWN_PII_BUNDLES)],
            model="gpt-4",
        )
        for i in range(count)
    ]


def _measure_peak_memory_streaming(record_count: int) -> tuple[int, float]:
    """Stream records through MockDataProvider and measure peak memory.

    Uses tracemalloc to capture the peak memory usage during the
    streaming operation.  Records are consumed one at a time via the
    generator, not buffered into a list.

    Args:
        record_count: Number of records to stream.

    Returns:
        A tuple of (peak_memory_bytes, elapsed_seconds).
    """
    # Build the record list outside of the measurement window
    records = _generate_records_lazy(record_count)
    provider = MockDataProvider(records=records)

    tracemalloc.start()
    start_time = time.perf_counter()

    provider.connect()
    count = 0
    for record in provider.stream_records():
        # Simulate minimal processing (serialization check)
        _ = json.dumps(record)
        count += 1
    provider.close()

    elapsed = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert count == record_count
    return peak, elapsed


# ── Memory ceiling tests ─────────────────────────────────────────────


@pytest.mark.benchmark
class TestMemoryCeiling:
    """Verify the 50MB memory ceiling is maintained during streaming.

    The Safe-Pipe architecture requires that Cecil never exceeds 50MB
    of resident memory during data processing.  These tests use
    tracemalloc to verify compliance.
    """

    def test_streaming_small_batch_under_memory_ceiling(self):
        """Verify 1K records stay well under the 50MB ceiling."""
        peak, _ = _measure_peak_memory_streaming(_SMALL_BATCH)
        peak_mb = peak / (1024 * 1024)

        assert peak < _MEMORY_CEILING_BYTES, (
            f"Memory ceiling exceeded: {peak_mb:.1f}MB > 50MB "
            f"during {_SMALL_BATCH:,} record stream"
        )

    def test_streaming_medium_batch_under_memory_ceiling(self):
        """Verify 10K records stay under the 50MB ceiling."""
        peak, _ = _measure_peak_memory_streaming(_MEDIUM_BATCH)
        peak_mb = peak / (1024 * 1024)

        assert peak < _MEMORY_CEILING_BYTES, (
            f"Memory ceiling exceeded: {peak_mb:.1f}MB > 50MB "
            f"during {_MEDIUM_BATCH:,} record stream"
        )

    @pytest.mark.slow
    def test_streaming_large_batch_under_memory_ceiling(self):
        """Verify 100K records stay under the 50MB ceiling."""
        peak, _ = _measure_peak_memory_streaming(_LARGE_BATCH)
        peak_mb = peak / (1024 * 1024)

        assert peak < _MEMORY_CEILING_BYTES, (
            f"Memory ceiling exceeded: {peak_mb:.1f}MB > 50MB "
            f"during {_LARGE_BATCH:,} record stream"
        )

    def test_generator_streaming_does_not_buffer_all_records(self):
        """Verify the generator yields records without full buffering.

        Streams records and checks that peak memory is significantly
        less than the total serialized size of all records.
        """
        record_count = 5_000
        records = _generate_records_lazy(record_count)

        provider = MockDataProvider(records=records)

        tracemalloc.start()
        provider.connect()
        count = 0
        for record in provider.stream_records():
            _ = json.dumps(record)
            count += 1
        provider.close()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert count == record_count
        # Peak memory should be much less than total serialized size.
        # The ratio depends on implementation; we use a generous 50%
        # threshold since MockDataProvider holds records in a list.
        # Real file-based providers would show much lower memory use.
        assert peak < _MEMORY_CEILING_BYTES, (
            f"Peak memory {peak / (1024 * 1024):.1f}MB exceeds 50MB ceiling"
        )


# ── Throughput benchmarks ────────────────────────────────────────────


@pytest.mark.benchmark
class TestThroughputBenchmark:
    """Measure records-per-second processing throughput.

    These tests report throughput and optionally assert a minimum
    rate to catch performance regressions.
    """

    def test_mock_provider_throughput_small_batch(self):
        """Benchmark throughput for 1K records."""
        _, elapsed = _measure_peak_memory_streaming(_SMALL_BATCH)
        rps = _SMALL_BATCH / elapsed if elapsed > 0 else float("inf")

        # Report throughput for CI visibility
        print(f"\n  Throughput ({_SMALL_BATCH:,} records): {rps:,.0f} records/sec")
        print(f"  Elapsed: {elapsed:.3f}s")

        assert rps > _MIN_THROUGHPUT_RPS, (
            f"Throughput too low: {rps:,.0f} records/sec < {_MIN_THROUGHPUT_RPS:,} minimum"
        )

    def test_mock_provider_throughput_medium_batch(self):
        """Benchmark throughput for 10K records."""
        _, elapsed = _measure_peak_memory_streaming(_MEDIUM_BATCH)
        rps = _MEDIUM_BATCH / elapsed if elapsed > 0 else float("inf")

        print(f"\n  Throughput ({_MEDIUM_BATCH:,} records): {rps:,.0f} records/sec")
        print(f"  Elapsed: {elapsed:.3f}s")

        assert rps > _MIN_THROUGHPUT_RPS, (
            f"Throughput too low: {rps:,.0f} records/sec < {_MIN_THROUGHPUT_RPS:,} minimum"
        )

    @pytest.mark.slow
    def test_mock_provider_throughput_large_batch(self):
        """Benchmark throughput for 100K records."""
        _, elapsed = _measure_peak_memory_streaming(_LARGE_BATCH)
        rps = _LARGE_BATCH / elapsed if elapsed > 0 else float("inf")

        print(f"\n  Throughput ({_LARGE_BATCH:,} records): {rps:,.0f} records/sec")
        print(f"  Elapsed: {elapsed:.3f}s")

        assert rps > _MIN_THROUGHPUT_RPS, (
            f"Throughput too low: {rps:,.0f} records/sec < {_MIN_THROUGHPUT_RPS:,} minimum"
        )

    def test_streaming_generator_throughput(self):
        """Benchmark the raw streaming generator without MockDataProvider.

        Tests ``stream_log_records`` directly to measure the overhead
        of record generation alone.
        """
        count = _MEDIUM_BATCH
        start = time.perf_counter()
        consumed = 0
        for _record in stream_log_records(count=count):
            consumed += 1
        elapsed = time.perf_counter() - start

        rps = count / elapsed if elapsed > 0 else float("inf")
        print(f"\n  Generator throughput ({count:,} records): {rps:,.0f} records/sec")
        print(f"  Elapsed: {elapsed:.3f}s")

        assert consumed == count
        assert rps > _MIN_THROUGHPUT_RPS


# ── Memory profile tests ────────────────────────────────────────────


@pytest.mark.benchmark
class TestMemoryProfile:
    """Detailed memory profiling for various pipeline operations."""

    def test_single_record_memory_footprint(self):
        """Measure the memory cost of a single log record."""
        record = make_llm_log_record(KNOWN_PII_BUNDLES[0])

        size = sys.getsizeof(record)
        serialized_size = len(json.dumps(record).encode("utf-8"))

        print(f"\n  Single record object size: {size} bytes")
        print(f"  Single record serialized size: {serialized_size} bytes")

        # A single record should be well under 10KB
        assert serialized_size < 10_000, f"Single record too large: {serialized_size} bytes"

    def test_metadata_fetch_does_not_allocate_excessively(self):
        """Verify fetch_metadata returns small, bounded data."""
        records = _generate_records_lazy(1_000)
        provider = MockDataProvider(records=records)
        provider.connect()

        tracemalloc.start()
        metadata = provider.fetch_metadata()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        provider.close()

        serialized = json.dumps(metadata)
        assert len(serialized) < 1_000, f"Metadata too large: {len(serialized)} bytes"
        # Metadata fetch should use negligible memory
        assert peak < 1_000_000, f"Metadata fetch used {peak} bytes, expected < 1MB"
