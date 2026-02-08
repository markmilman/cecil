"""Streaming integration tests for LocalFileProvider.

Verifies the full provider lifecycle (construct, connect, stream, close)
for all supported formats, PII leak detection in error paths and
metadata, and context manager behavior.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from cecil.core.providers.local_file import LocalFileProvider
from tests.fixtures.pii_samples import (
    KNOWN_PII_BUNDLES,
    all_known_pii_values,
    generate_sample_csv,
    generate_sample_jsonl,
    generate_sample_parquet,
)


# ---- Helpers ----------------------------------------------------------------


def _assert_no_pii_in_text(text: str, pii_values: list[str]) -> None:
    """Assert that none of the known PII values appear in the text.

    Args:
        text: The text to scan for PII leaks.
        pii_values: The list of PII strings that must be absent.

    Raises:
        AssertionError: If any PII value is found in the text.
    """
    for value in pii_values:
        assert value not in text, (
            f"PII LEAK DETECTED: '{value}' found in output. Safe-Pipe invariant violated."
        )


# ---- Full lifecycle tests ---------------------------------------------------


class TestLocalFileProviderStreamingLifecycle:
    """Verify construct -> connect -> stream -> close lifecycle for all formats."""

    def test_full_lifecycle_jsonl(self, tmp_path: Path) -> None:
        """Construct, connect, stream all records, close for JSONL."""
        path = tmp_path / "lifecycle.jsonl"
        record_count = 20
        generate_sample_jsonl(str(path), count=record_count)

        provider = LocalFileProvider(file_path=path)
        provider.connect()

        records: list[dict[str, Any]] = []
        for record in provider.stream_records():
            records.append(record)

        provider.close()

        assert len(records) == record_count
        for record in records:
            assert isinstance(record, dict)
            # JSONL records from pii_samples include these keys
            assert "model" in record
            assert "timestamp" in record

    def test_full_lifecycle_csv(self, tmp_path: Path) -> None:
        """Construct, connect, stream all records, close for CSV."""
        path = tmp_path / "lifecycle.csv"
        record_count = 15
        generate_sample_csv(str(path), count=record_count)

        provider = LocalFileProvider(file_path=path)
        provider.connect()

        records: list[dict[str, Any]] = []
        for record in provider.stream_records():
            records.append(record)

        provider.close()

        assert len(records) == record_count
        for record in records:
            assert isinstance(record, dict)
            # CSV records from pii_samples include these keys
            assert "email" in record
            assert "name" in record

    def test_full_lifecycle_parquet(self, tmp_path: Path) -> None:
        """Construct, connect, stream all records, close for Parquet."""
        path = tmp_path / "lifecycle.parquet"
        record_count = 12
        generate_sample_parquet(str(path), count=record_count)

        provider = LocalFileProvider(file_path=path)
        provider.connect()

        records: list[dict[str, Any]] = []
        for record in provider.stream_records():
            records.append(record)

        provider.close()

        assert len(records) == record_count
        for record in records:
            assert isinstance(record, dict)
            assert "email" in record
            assert "name" in record

    def test_context_manager_lifecycle(self, tmp_path: Path) -> None:
        """Using ``with`` statement connects, streams, and closes correctly."""
        path = tmp_path / "ctx.jsonl"
        record_count = 8
        generate_sample_jsonl(str(path), count=record_count)

        records: list[dict[str, Any]] = []
        with LocalFileProvider(file_path=path) as provider:
            for record in provider.stream_records():
                records.append(record)

            # Inside the context, file handle is open
            assert provider._file_handle is not None

        # Outside the context, file handle is closed
        assert provider._file_handle is None
        assert len(records) == record_count


# ---- PII leak detection tests -----------------------------------------------


class TestLocalFileProviderPIILeakDetection:
    """Verify no PII leaks through error messages, quarantine logs, or metadata."""

    def test_error_messages_contain_no_pii(self, tmp_path: Path) -> None:
        """Trigger errors with PII-laden data, verify no PII in error strings.

        Creates a JSONL file with PII embedded in malformed lines to
        ensure that when the provider skips bad records, the error/log
        messages do not include the raw PII content.
        """
        pii_values = all_known_pii_values()
        path = tmp_path / "pii_errors.jsonl"

        # Build malformed lines that contain PII but are not valid JSON.
        lines: list[str] = []
        for bundle in KNOWN_PII_BUNDLES:
            # Valid record
            lines.append(json.dumps({"id": 1, "safe": "ok"}))
            # Malformed line stuffed with PII
            lines.append(f"NOT JSON {bundle.email} {bundle.ssn} {bundle.phone}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        quarantine = tmp_path / "quarantine.jsonl"
        provider = LocalFileProvider(
            file_path=path,
            quarantine_path=quarantine,
        )

        with provider:
            records = list(provider.stream_records())

        # We should have gotten the valid records
        assert len(records) == len(KNOWN_PII_BUNDLES)

        # Check quarantine output for PII leaks
        if quarantine.exists():
            quarantine_text = quarantine.read_text(encoding="utf-8")
            _assert_no_pii_in_text(quarantine_text, pii_values)

    def test_quarantine_log_contains_no_pii(self, tmp_path: Path) -> None:
        """Create malformed records with PII, verify quarantine has no PII.

        Each quarantine entry should only contain structural metadata
        (line number, error type, timestamp, source file) -- never raw
        record content.
        """
        pii_values = all_known_pii_values()
        path = tmp_path / "pii_quarantine.jsonl"

        # Build a file where every other line is malformed and contains PII.
        lines: list[str] = []
        for bundle in KNOWN_PII_BUNDLES:
            lines.append(json.dumps({"safe": True}))
            # Malformed line with all PII fields
            lines.append(
                f"BROKEN {bundle.name} {bundle.email} "
                f"{bundle.ssn} {bundle.credit_card} "
                f"{bundle.ip_address} {bundle.address}"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        quarantine = tmp_path / "quarantine.jsonl"
        provider = LocalFileProvider(
            file_path=path,
            quarantine_path=quarantine,
        )

        with provider:
            list(provider.stream_records())

        assert quarantine.exists(), "Quarantine file should have been created"
        quarantine_text = quarantine.read_text(encoding="utf-8")

        # Verify quarantine has entries
        entries = [
            json.loads(line) for line in quarantine_text.strip().split("\n") if line.strip()
        ]
        assert len(entries) == len(KNOWN_PII_BUNDLES)

        # Verify no PII in quarantine text
        _assert_no_pii_in_text(quarantine_text, pii_values)

        # Verify each entry has only safe structural keys
        safe_keys = {"line_number", "error_type", "timestamp", "source_file"}
        for entry in entries:
            assert set(entry.keys()) == safe_keys, (
                f"Quarantine entry has unexpected keys: {set(entry.keys()) - safe_keys}"
            )

    def test_fetch_metadata_contains_no_pii(self, tmp_path: Path) -> None:
        """Serialize metadata dict, verify no PII values appear.

        The metadata returned by ``fetch_metadata()`` should contain
        only provider info, file path, size, format, and record counts.
        No PII from the file content should leak into metadata.
        """
        pii_values = all_known_pii_values()
        path = tmp_path / "pii_meta.jsonl"
        generate_sample_jsonl(str(path), count=20)

        with LocalFileProvider(file_path=path) as provider:
            # Stream all records to populate record_count
            for _record in provider.stream_records():
                pass
            metadata = provider.fetch_metadata()

        # Serialize the entire metadata dict and check for PII
        metadata_text = json.dumps(metadata, default=str)
        _assert_no_pii_in_text(metadata_text, pii_values)

        # Verify expected keys are present
        assert metadata["provider"] == "local_file"
        assert metadata["format"] == "jsonl"
        assert metadata["record_count"] == 20
        assert metadata["file_size_bytes"] is not None

    def test_log_output_contains_no_pii(
        self,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Capture log output during streaming, verify no PII.

        Streams PII-laden data through the provider and checks that
        all log messages emitted during the process are PII-free.
        """
        pii_values = all_known_pii_values()
        path = tmp_path / "pii_logs.jsonl"

        # Create a file with valid PII records and some malformed ones.
        lines: list[str] = []
        for bundle in KNOWN_PII_BUNDLES:
            lines.append(
                json.dumps(
                    {
                        "email": bundle.email,
                        "name": bundle.name,
                        "ssn": bundle.ssn,
                    }
                )
            )
            # Malformed line with PII
            lines.append(f"BAD LINE {bundle.email} {bundle.ssn}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        quarantine = tmp_path / "quarantine.jsonl"

        with (
            caplog.at_level(logging.DEBUG, logger="cecil.core.providers.local_file"),
            LocalFileProvider(
                file_path=path,
                quarantine_path=quarantine,
            ) as provider,
        ):
            list(provider.stream_records())

        # Check all captured log messages for PII
        full_log_text = caplog.text
        _assert_no_pii_in_text(full_log_text, pii_values)

    def test_fetch_metadata_parquet_contains_no_pii(self, tmp_path: Path) -> None:
        """Verify Parquet metadata also contains no PII values."""
        pii_values = all_known_pii_values()
        path = tmp_path / "pii_meta.parquet"
        generate_sample_parquet(str(path), count=10)

        with LocalFileProvider(file_path=path) as provider:
            for _record in provider.stream_records():
                pass
            metadata = provider.fetch_metadata()

        metadata_text = json.dumps(metadata, default=str)
        _assert_no_pii_in_text(metadata_text, pii_values)

    def test_fetch_metadata_csv_contains_no_pii(self, tmp_path: Path) -> None:
        """Verify CSV metadata also contains no PII values."""
        pii_values = all_known_pii_values()
        path = tmp_path / "pii_meta.csv"
        generate_sample_csv(str(path), count=10)

        with LocalFileProvider(file_path=path) as provider:
            for _record in provider.stream_records():
                pass
            metadata = provider.fetch_metadata()

        metadata_text = json.dumps(metadata, default=str)
        _assert_no_pii_in_text(metadata_text, pii_values)
