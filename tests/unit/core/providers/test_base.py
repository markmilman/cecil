"""Unit tests for BaseDataProvider ABC and MockDataProvider."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.mock import MockDataProvider


# ── ABC contract tests ─────────────────────────────────────────────────


class TestBaseDataProviderABC:
    """Verify the ABC enforces the expected interface."""

    def test_cannot_instantiate_abstract_base(self):
        with pytest.raises(TypeError, match="abstract method"):
            BaseDataProvider()  # type: ignore[abstract]

    def test_incomplete_subclass_missing_stream_records_raises(self):
        class PartialProvider(BaseDataProvider):
            def connect(self) -> None: ...
            def close(self) -> None: ...
            def fetch_metadata(self) -> dict[str, Any]:
                return {}

        with pytest.raises(TypeError, match="stream_records"):
            PartialProvider()  # type: ignore[abstract]

    def test_incomplete_subclass_missing_connect_raises(self):
        class PartialProvider(BaseDataProvider):
            def stream_records(self) -> Generator[dict[str, Any], None, None]:
                yield {}

            def close(self) -> None: ...
            def fetch_metadata(self) -> dict[str, Any]:
                return {}

        with pytest.raises(TypeError, match="connect"):
            PartialProvider()  # type: ignore[abstract]

    def test_incomplete_subclass_missing_close_raises(self):
        class PartialProvider(BaseDataProvider):
            def connect(self) -> None: ...
            def stream_records(self) -> Generator[dict[str, Any], None, None]:
                yield {}

            def fetch_metadata(self) -> dict[str, Any]:
                return {}

        with pytest.raises(TypeError, match="close"):
            PartialProvider()  # type: ignore[abstract]

    def test_incomplete_subclass_missing_fetch_metadata_raises(self):
        class PartialProvider(BaseDataProvider):
            def connect(self) -> None: ...
            def stream_records(self) -> Generator[dict[str, Any], None, None]:
                yield {}

            def close(self) -> None: ...

        with pytest.raises(TypeError, match="fetch_metadata"):
            PartialProvider()  # type: ignore[abstract]


# ── MockDataProvider tests ─────────────────────────────────────────────


class TestMockDataProvider:
    """Verify MockDataProvider implements the BaseDataProvider contract."""

    def test_is_subclass_of_base_data_provider(self):
        assert issubclass(MockDataProvider, BaseDataProvider)

    def test_connect_sets_connected_flag(self):
        provider = MockDataProvider()
        assert not provider.connected
        provider.connect()
        assert provider.connected

    def test_close_clears_connected_flag(self):
        provider = MockDataProvider()
        provider.connect()
        provider.close()
        assert not provider.connected

    def test_stream_records_yields_all_records(self):
        records = [
            {"user": "alice@example.com", "model": "gpt-4"},
            {"user": "bob@example.com", "model": "claude-3"},
        ]
        provider = MockDataProvider(records=records)
        result = list(provider.stream_records())
        assert result == records

    def test_stream_records_returns_generator(self):
        provider = MockDataProvider(records=[{"a": "1"}])
        gen = provider.stream_records()
        assert isinstance(gen, Generator)

    def test_stream_records_with_empty_list_yields_nothing(self):
        provider = MockDataProvider(records=[])
        result = list(provider.stream_records())
        assert result == []

    def test_stream_records_with_no_records_arg_yields_nothing(self):
        provider = MockDataProvider()
        result = list(provider.stream_records())
        assert result == []

    def test_fetch_metadata_includes_provider_key(self):
        provider = MockDataProvider()
        meta = provider.fetch_metadata()
        assert meta["provider"] == "mock"

    def test_fetch_metadata_includes_record_count(self):
        provider = MockDataProvider(records=[{"a": "1"}, {"b": "2"}])
        meta = provider.fetch_metadata()
        assert meta["record_count"] == 2

    def test_fetch_metadata_merges_custom_metadata(self):
        provider = MockDataProvider(metadata={"source": "test-suite"})
        meta = provider.fetch_metadata()
        assert meta["source"] == "test-suite"
        assert meta["provider"] == "mock"

    def test_context_manager_connects_and_closes(self):
        provider = MockDataProvider()
        with provider:
            assert provider.connected
        assert not provider.connected

    def test_context_manager_closes_on_exception(self):
        provider = MockDataProvider()
        with pytest.raises(RuntimeError), provider:
            assert provider.connected
            raise RuntimeError("boom")
        assert not provider.connected

    def test_stream_records_yields_records_lazily(self):
        """Verify records are yielded one at a time, not collected."""
        records = [{"i": str(i)} for i in range(100)]
        provider = MockDataProvider(records=records)
        gen = provider.stream_records()

        first = next(gen)
        assert first == {"i": "0"}

        second = next(gen)
        assert second == {"i": "1"}
