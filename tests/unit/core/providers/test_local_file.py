"""Unit tests for LocalFileProvider."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest

from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.local_file import LocalFileProvider
from cecil.utils.errors import ProviderConnectionError, ProviderReadError


# ── Constructor and format detection ──────────────────────────────────


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


# ── connect() ─────────────────────────────────────────────────────────


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


# ── close() ───────────────────────────────────────────────────────────


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


# ── Context manager ───────────────────────────────────────────────────


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


# ── stream_records() JSONL ────────────────────────────────────────────


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

    def test_stream_records_on_empty_file(self, empty_jsonl_path: Path) -> None:
        with LocalFileProvider(file_path=empty_jsonl_path) as provider:
            records = list(provider.stream_records())
        assert records == []

    def test_stream_records_raises_on_malformed_json(
        self,
        malformed_jsonl_path: Path,
    ) -> None:
        with LocalFileProvider(file_path=malformed_jsonl_path) as provider:
            gen = provider.stream_records()
            # First two records are valid
            next(gen)
            next(gen)
            # Third line is invalid
            with pytest.raises(ProviderReadError, match="Invalid JSON on line 3"):
                next(gen)

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


# ── stream_records() unsupported formats ──────────────────────────────


class TestLocalFileProviderUnsupportedFormats:
    """Verify NotImplementedError for non-JSONL formats."""

    def test_csv_format_raises_not_implemented(self, tmp_csv_path: Path) -> None:
        with (
            LocalFileProvider(file_path=tmp_csv_path) as provider,
            pytest.raises(NotImplementedError, match="csv"),
        ):
            list(provider.stream_records())

    def test_parquet_format_raises_not_implemented(self, tmp_path: Path) -> None:
        path = tmp_path / "data.parquet"
        path.write_bytes(b"dummy")
        with (
            LocalFileProvider(file_path=path) as provider,
            pytest.raises(NotImplementedError, match="parquet"),
        ):
            list(provider.stream_records())


# ── fetch_metadata() ──────────────────────────────────────────────────


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


# ── Registry integration ──────────────────────────────────────────────


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
