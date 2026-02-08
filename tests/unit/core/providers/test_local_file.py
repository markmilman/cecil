"""Unit tests for LocalFileProvider."""

from __future__ import annotations

import csv
import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.local_file import LocalFileProvider
from cecil.utils.errors import (
    ProviderConnectionError,
    ProviderDependencyError,
)


# -- Constructor and format detection --------------------------------------


class TestLocalFileProviderInit:
    """Verify constructor and format auto-detection."""

    def test_is_subclass_of_base_data_provider(self) -> None:
        assert issubclass(LocalFileProvider, BaseDataProvider)

    def test_accepts_string_path(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=str(tmp_jsonl_path))
        assert provider.file_path == tmp_jsonl_path

    def test_accepts_path_object(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        assert provider.file_path == tmp_jsonl_path

    def test_detects_jsonl_format_from_extension(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        assert provider.format == "jsonl"

    def test_detects_csv_format_from_extension(self, tmp_csv_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_csv_path)
        assert provider.format == "csv"

    def test_format_hint_overrides_extension(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path, format_hint="csv")
        assert provider.format == "csv"

    def test_format_hint_is_lowercased(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path, format_hint="JSONL")
        assert provider.format == "jsonl"

    def test_unknown_extension_without_hint_raises(self, tmp_path: Path) -> None:
        unknown_file = tmp_path / "data.xyz"
        with pytest.raises(ProviderConnectionError, match="Cannot detect format"):
            LocalFileProvider(file_path=unknown_file)

    def test_unknown_extension_with_hint_succeeds(self, tmp_path: Path) -> None:
        unknown_file = tmp_path / "data.xyz"
        provider = LocalFileProvider(file_path=unknown_file, format_hint="jsonl")
        assert provider.format == "jsonl"


# -- connect() -------------------------------------------------------------


class TestLocalFileProviderConnect:
    """Verify connect() validates the file and opens a handle."""

    def test_connect_succeeds_for_valid_file(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        provider.connect()
        provider.close()

    def test_connect_raises_for_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.jsonl"
        provider = LocalFileProvider(file_path=missing)
        with pytest.raises(ProviderConnectionError, match="File not found"):
            provider.connect()

    def test_connect_raises_for_directory(self, tmp_path: Path) -> None:
        directory = tmp_path / "subdir"
        directory.mkdir()
        # Need format_hint since .mkdir has no extension
        provider = LocalFileProvider(file_path=directory, format_hint="jsonl")
        with pytest.raises(ProviderConnectionError, match="not a regular file"):
            provider.connect()

    def test_connect_raises_for_unreadable_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        path = tmp_path / "secret.jsonl"
        path.write_text("{}", encoding="utf-8")
        # Monkeypatch os.access to simulate permission denied
        import os

        monkeypatch.setattr(os, "access", lambda p, m: False)
        provider = LocalFileProvider(file_path=path)
        with pytest.raises(ProviderConnectionError, match="not readable"):
            provider.connect()

    def test_connect_raises_for_empty_file(self, tmp_path: Path) -> None:
        """Zero-byte file is rejected at connect time."""
        path = tmp_path / "empty.jsonl"
        path.write_text("", encoding="utf-8")
        provider = LocalFileProvider(file_path=path)
        with pytest.raises(ProviderConnectionError, match=r"empty.*zero bytes"):
            provider.connect()

    def test_connect_validates_jsonl_content(self, tmp_path: Path) -> None:
        """A .jsonl file with non-JSON content is rejected at connect."""
        path = tmp_path / "bad.jsonl"
        path.write_text("this is not json\nanother line\n", encoding="utf-8")
        provider = LocalFileProvider(file_path=path)
        with pytest.raises(
            ProviderConnectionError,
            match="does not appear to be valid JSONL",
        ):
            provider.connect()

    def test_connect_validates_csv_content(self, tmp_path: Path) -> None:
        """A .csv file that is actually a binary blob is rejected."""
        path = tmp_path / "bad.csv"
        # Build binary content with null bytes to simulate a PNG file
        binary_data = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        binary_data += bytes([0x00, 0x00, 0x00]) + b"binary content"
        path.write_bytes(binary_data)
        provider = LocalFileProvider(file_path=path)
        with pytest.raises(
            ProviderConnectionError,
            match="does not appear to be valid CSV",
        ):
            provider.connect()

    def test_connect_validates_parquet_content(self, tmp_path: Path) -> None:
        """A .parquet file without PAR1 magic bytes is rejected."""
        path = tmp_path / "bad.parquet"
        path.write_bytes(b"NOT_PARQUET_DATA_HERE")
        provider = LocalFileProvider(file_path=path)
        with pytest.raises(
            ProviderConnectionError,
            match="missing PAR1 magic bytes",
        ):
            provider.connect()

    def test_format_mismatch_jsonl_extension_csv_content(
        self,
        tmp_path: Path,
    ) -> None:
        """A .jsonl file containing CSV content is detected and rejected."""
        path = tmp_path / "mismatch.jsonl"
        path.write_text("name,age,city\nAlice,30,Portland\n", encoding="utf-8")
        provider = LocalFileProvider(file_path=path)
        with pytest.raises(
            ProviderConnectionError,
            match="does not appear to be valid JSONL",
        ):
            provider.connect()


# -- close() ---------------------------------------------------------------


class TestLocalFileProviderClose:
    """Verify close() releases resources safely."""

    def test_close_after_connect(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        provider.connect()
        provider.close()
        # Should not raise on second close
        provider.close()

    def test_close_without_connect(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        # Should not raise
        provider.close()


# -- Context manager -------------------------------------------------------


class TestLocalFileProviderContextManager:
    """Verify with-statement support via inherited __enter__/__exit__."""

    def test_context_manager_connects_and_closes(
        self,
        tmp_jsonl_path: Path,
    ) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        with provider:
            # File handle should be open
            assert provider._file_handle is not None
        # File handle should be closed
        assert provider._file_handle is None

    def test_context_manager_closes_on_exception(
        self,
        tmp_jsonl_path: Path,
    ) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        with pytest.raises(RuntimeError), provider:
            raise RuntimeError("boom")
        assert provider._file_handle is None


# -- stream_records() JSONL ------------------------------------------------


class TestLocalFileProviderStreamJSONL:
    """Verify JSONL streaming behavior."""

    def test_stream_records_returns_generator(self, tmp_jsonl_path: Path) -> None:
        with LocalFileProvider(file_path=tmp_jsonl_path) as provider:
            gen = provider.stream_records()
            assert isinstance(gen, Generator)

    def test_stream_records_yields_all_records(self, tmp_jsonl_path: Path) -> None:
        with LocalFileProvider(file_path=tmp_jsonl_path) as provider:
            records = list(provider.stream_records())
        assert len(records) == 5

    def test_stream_records_yields_dicts(self, tmp_jsonl_path: Path) -> None:
        with LocalFileProvider(file_path=tmp_jsonl_path) as provider:
            for record in provider.stream_records():
                assert isinstance(record, dict)

    def test_stream_records_lazy_yielding(self, tmp_jsonl_path: Path) -> None:
        """Verify records are yielded one at a time, not collected."""
        with LocalFileProvider(file_path=tmp_jsonl_path) as provider:
            gen = provider.stream_records()
            first = next(gen)
            assert isinstance(first, dict)
            second = next(gen)
            assert isinstance(second, dict)

    def test_stream_records_skips_blank_lines(
        self,
        blank_lines_jsonl_path: Path,
    ) -> None:
        with LocalFileProvider(file_path=blank_lines_jsonl_path) as provider:
            records = list(provider.stream_records())
        assert len(records) == 2
        assert records[0] == {"id": 1}
        assert records[1] == {"id": 2}

    def test_stream_jsonl_skips_malformed_records(
        self,
        malformed_jsonl_path: Path,
    ) -> None:
        """Malformed JSON lines are skipped, not raised."""
        with LocalFileProvider(file_path=malformed_jsonl_path) as provider:
            records = list(provider.stream_records())
        # Two valid records out of three lines
        assert len(records) == 2
        assert records[0] == {"id": 1, "value": "ok"}
        assert records[1] == {"id": 2, "value": "also ok"}

    def test_stream_records_preserves_record_data(self, tmp_path: Path) -> None:
        path = tmp_path / "precise.jsonl"
        expected = [
            {"name": "alice", "age": 30},
            {"name": "bob", "age": 25},
        ]
        path.write_text(
            "\n".join(json.dumps(r) for r in expected) + "\n",
            encoding="utf-8",
        )
        with LocalFileProvider(file_path=path) as provider:
            records = list(provider.stream_records())
        assert records == expected


# -- stream_records() CSV --------------------------------------------------


class TestLocalFileProviderStreamCSV:
    """Verify CSV streaming behavior."""

    def test_stream_records_csv_yields_all_records(
        self,
        tmp_csv_path: Path,
    ) -> None:
        """Basic CSV with 5 rows yields exactly 5 records."""
        with LocalFileProvider(file_path=tmp_csv_path) as provider:
            records = list(provider.stream_records())
        assert len(records) == 5

    def test_stream_records_csv_yields_dicts(self, tmp_csv_path: Path) -> None:
        """Each CSV record is yielded as a dict."""
        with LocalFileProvider(file_path=tmp_csv_path) as provider:
            for record in provider.stream_records():
                assert isinstance(record, dict)

    def test_stream_records_csv_with_custom_delimiter(
        self,
        tmp_path: Path,
    ) -> None:
        """TSV file with delimiter=tab is read correctly."""
        path = tmp_path / "data.csv"
        path.write_text(
            "name\tage\tcity\nAlice\t30\tPortland\nBob\t25\tChicago\n",
            encoding="utf-8",
        )
        with LocalFileProvider(
            file_path=path,
            delimiter="\t",
        ) as provider:
            records = list(provider.stream_records())
        assert len(records) == 2
        assert records[0] == {"name": "Alice", "age": "30", "city": "Portland"}
        assert records[1] == {"name": "Bob", "age": "25", "city": "Chicago"}

    def test_stream_records_csv_header_only(self, tmp_path: Path) -> None:
        """CSV file with only a header row yields nothing."""
        path = tmp_path / "header_only.csv"
        path.write_text("name,age,city\n", encoding="utf-8")
        with LocalFileProvider(file_path=path) as provider:
            records = list(provider.stream_records())
        assert records == []

    def test_stream_records_csv_quoted_fields(self, tmp_path: Path) -> None:
        """Fields containing commas and newlines are handled correctly."""
        path = tmp_path / "quoted.csv"
        # Use csv.writer to produce correct quoting
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["name", "bio", "city"])
            writer.writerow(["Alice", "Loves coding, hiking", "Portland"])
            writer.writerow(["Bob", "Line1\nLine2", "Chicago"])
        with LocalFileProvider(file_path=path) as provider:
            records = list(provider.stream_records())
        assert len(records) == 2
        assert records[0]["bio"] == "Loves coding, hiking"
        assert records[1]["bio"] == "Line1\nLine2"

    def test_stream_records_csv_skips_empty_rows(self, tmp_path: Path) -> None:
        """Blank lines interspersed in a CSV are skipped."""
        path = tmp_path / "blanks.csv"
        path.write_text(
            "name,age\nAlice,30\n\n  ,  \nBob,25\n",
            encoding="utf-8",
        )
        with LocalFileProvider(file_path=path) as provider:
            records = list(provider.stream_records())
        assert len(records) == 2
        assert records[0]["name"] == "Alice"
        assert records[1]["name"] == "Bob"

    def test_csv_format_no_longer_raises_not_implemented(
        self,
        tmp_csv_path: Path,
    ) -> None:
        """Verify CSV streaming does not raise NotImplementedError."""
        with LocalFileProvider(file_path=tmp_csv_path) as provider:
            # Should not raise NotImplementedError
            records = list(provider.stream_records())
        assert len(records) > 0

    def test_stream_csv_skips_malformed_records(self, tmp_path: Path) -> None:
        """Badly formed CSV rows are handled gracefully."""
        path = tmp_path / "bad_csv.csv"
        # Write a valid header then a row with mismatched fields
        content = "name,age,city\nAlice,30,Portland\n,,,extra,too_many\nBob,25,Chicago\n"
        path.write_text(content, encoding="utf-8")
        with LocalFileProvider(file_path=path) as provider:
            records = list(provider.stream_records())
        # Alice and Bob should be present
        assert any(r.get("name") == "Alice" for r in records)
        assert any(r.get("name") == "Bob" for r in records)


# -- stream_records() unsupported formats ----------------------------------


class TestLocalFileProviderUnsupportedFormats:
    """Verify NotImplementedError for formats not yet implemented."""

    def test_unknown_format_raises_not_implemented(self, tmp_path: Path) -> None:
        path = tmp_path / "data.xyz"
        path.write_text("dummy", encoding="utf-8")
        with (
            LocalFileProvider(file_path=path, format_hint="xyz") as provider,
            pytest.raises(NotImplementedError, match="xyz"),
        ):
            list(provider.stream_records())


# -- stream_records() Parquet ----------------------------------------------


class TestLocalFileProviderStreamParquet:
    """Verify Parquet streaming behavior."""

    def test_stream_records_parquet_yields_all_records(
        self,
        tmp_parquet_path: Path,
    ) -> None:
        """All rows in the Parquet file are yielded."""
        with LocalFileProvider(file_path=tmp_parquet_path) as provider:
            records = list(provider.stream_records())
        assert len(records) == 5

    def test_stream_records_parquet_yields_dicts(
        self,
        tmp_parquet_path: Path,
    ) -> None:
        """Each yielded record is a plain Python dict."""
        with LocalFileProvider(file_path=tmp_parquet_path) as provider:
            for record in provider.stream_records():
                assert isinstance(record, dict)

    def test_stream_records_parquet_preserves_types(
        self,
        tmp_parquet_path: Path,
    ) -> None:
        """Python-native types are returned after .as_py() conversion."""
        with LocalFileProvider(file_path=tmp_parquet_path) as provider:
            first = next(provider.stream_records())
        # String columns
        assert isinstance(first["email"], str)
        assert isinstance(first["name"], str)
        # Integer column
        assert isinstance(first["tokens_in"], int)
        # Float column
        assert isinstance(first["cost_usd"], float)

    def test_parquet_without_pyarrow_raises_dependency_error(
        self,
        tmp_parquet_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ProviderDependencyError is raised when pyarrow is not installed."""
        import builtins

        real_import = builtins.__import__

        def mock_import(
            name: str,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            if name == "pyarrow.parquet" or name == "pyarrow":
                raise ImportError("mocked missing pyarrow")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with (
            LocalFileProvider(file_path=tmp_parquet_path) as provider,
            pytest.raises(
                ProviderDependencyError,
                match="pyarrow",
            ),
        ):
            list(provider.stream_records())

    def test_parquet_format_no_longer_raises_not_implemented(
        self,
        tmp_parquet_path: Path,
    ) -> None:
        """Parquet format is handled without raising NotImplementedError."""
        with LocalFileProvider(file_path=tmp_parquet_path) as provider:
            records = list(provider.stream_records())
        assert len(records) > 0

    def test_parquet_record_count_updated_after_streaming(
        self,
        tmp_parquet_path: Path,
    ) -> None:
        """fetch_metadata() reflects the correct record count after streaming."""
        with LocalFileProvider(file_path=tmp_parquet_path) as provider:
            list(provider.stream_records())
            meta = provider.fetch_metadata()
        assert meta["record_count"] == 5
        assert meta["format"] == "parquet"


# -- Quarantine logging ----------------------------------------------------


class TestLocalFileProviderQuarantine:
    """Verify quarantine log behavior for malformed records."""

    def test_stream_jsonl_quarantine_writes_record(
        self,
        malformed_jsonl_path: Path,
        tmp_path: Path,
    ) -> None:
        """Quarantine log file contains an entry for each bad record."""
        quarantine = tmp_path / "quarantine.jsonl"
        provider = LocalFileProvider(
            file_path=malformed_jsonl_path,
            quarantine_path=quarantine,
        )
        with provider:
            list(provider.stream_records())

        assert quarantine.exists()
        entries = [
            json.loads(line) for line in quarantine.read_text(encoding="utf-8").strip().split("\n")
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["line_number"] == 3
        assert entry["error_type"] == "JSONDecodeError"
        assert "timestamp" in entry
        assert entry["source_file"] == str(malformed_jsonl_path)

    def test_stream_jsonl_quarantine_no_pii(
        self,
        tmp_path: Path,
    ) -> None:
        """Quarantine log must NOT contain any raw data or PII values."""
        path = tmp_path / "pii.jsonl"
        pii_email = "secret@example.com"
        pii_ssn = "123-45-6789"
        lines_data = [
            json.dumps({"email": pii_email, "id": 1}),
            '{"bad json with PII ' + pii_email + " and SSN " + pii_ssn,
            json.dumps({"email": "other@example.com", "id": 2}),
        ]
        path.write_text("\n".join(lines_data) + "\n", encoding="utf-8")

        quarantine = tmp_path / "quarantine.jsonl"
        provider = LocalFileProvider(
            file_path=path,
            quarantine_path=quarantine,
        )
        with provider:
            list(provider.stream_records())

        quarantine_text = quarantine.read_text(encoding="utf-8")
        # No PII should appear in quarantine
        assert pii_email not in quarantine_text
        assert pii_ssn not in quarantine_text
        # But the structural metadata should be there
        entry = json.loads(quarantine_text.strip())
        assert entry["line_number"] == 2
        assert entry["error_type"] == "JSONDecodeError"

    def test_quarantine_disabled_by_default(
        self,
        malformed_jsonl_path: Path,
        tmp_path: Path,
    ) -> None:
        """When no quarantine_path is given, no quarantine file is created."""
        quarantine = tmp_path / "should_not_exist.jsonl"
        provider = LocalFileProvider(file_path=malformed_jsonl_path)
        with provider:
            list(provider.stream_records())

        assert not quarantine.exists()

    def test_metadata_includes_quarantined_count(
        self,
        malformed_jsonl_path: Path,
        tmp_path: Path,
    ) -> None:
        """fetch_metadata() includes records_quarantined after streaming."""
        quarantine = tmp_path / "quarantine.jsonl"
        provider = LocalFileProvider(
            file_path=malformed_jsonl_path,
            quarantine_path=quarantine,
        )
        with provider:
            list(provider.stream_records())
            meta = provider.fetch_metadata()

        assert meta["records_quarantined"] == 1
        assert meta["record_count"] == 2

    def test_metadata_quarantined_count_zero_by_default(
        self,
        tmp_jsonl_path: Path,
    ) -> None:
        """records_quarantined is zero when no malformed records exist."""
        with LocalFileProvider(file_path=tmp_jsonl_path) as provider:
            list(provider.stream_records())
            meta = provider.fetch_metadata()
        assert meta["records_quarantined"] == 0


# -- fetch_metadata() ------------------------------------------------------


class TestLocalFileProviderFetchMetadata:
    """Verify metadata reporting."""

    def test_metadata_includes_provider_key(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        meta = provider.fetch_metadata()
        assert meta["provider"] == "local_file"

    def test_metadata_includes_file_path(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        meta = provider.fetch_metadata()
        assert meta["file_path"] == str(tmp_jsonl_path)

    def test_metadata_includes_format(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        meta = provider.fetch_metadata()
        assert meta["format"] == "jsonl"

    def test_metadata_includes_file_size(self, tmp_jsonl_path: Path) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        meta = provider.fetch_metadata()
        assert meta["file_size_bytes"] is not None
        assert meta["file_size_bytes"] > 0

    def test_metadata_record_count_zero_before_streaming(
        self,
        tmp_jsonl_path: Path,
    ) -> None:
        provider = LocalFileProvider(file_path=tmp_jsonl_path)
        meta = provider.fetch_metadata()
        assert meta["record_count"] == 0

    def test_metadata_record_count_updated_after_streaming(
        self,
        tmp_jsonl_path: Path,
    ) -> None:
        with LocalFileProvider(file_path=tmp_jsonl_path) as provider:
            list(provider.stream_records())
            meta = provider.fetch_metadata()
        assert meta["record_count"] == 5

    def test_metadata_file_size_none_for_missing_file(
        self,
        tmp_path: Path,
    ) -> None:
        missing = tmp_path / "gone.jsonl"
        provider = LocalFileProvider(file_path=missing)
        meta = provider.fetch_metadata()
        assert meta["file_size_bytes"] is None


# -- Registry integration -------------------------------------------------


class TestLocalFileProviderRegistry:
    """Verify the provider is registered in the global registry."""

    def test_local_file_in_registry(self) -> None:
        from cecil.core.providers.registry import list_providers

        assert "local_file" in list_providers()

    def test_get_provider_returns_local_file_instance(
        self,
        tmp_jsonl_path: Path,
    ) -> None:
        from cecil.core.providers.registry import get_provider

        provider = get_provider("local_file", file_path=tmp_jsonl_path)
        assert isinstance(provider, LocalFileProvider)

    def test_importable_from_package_init(self) -> None:
        from cecil.core.providers import LocalFileProvider as LocalFileProviderImport

        assert LocalFileProviderImport is LocalFileProvider
