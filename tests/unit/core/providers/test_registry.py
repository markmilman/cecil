"""Unit tests for the provider registry."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.mock import MockDataProvider
from cecil.core.providers.registry import (
    PROVIDER_REGISTRY,
    get_provider,
    list_providers,
    register_provider,
)


class _DummyProvider(BaseDataProvider):
    """Minimal concrete provider for registry tests."""

    def connect(self) -> None: ...
    def stream_records(self) -> Generator[dict[str, Any], None, None]:
        yield {}

    def close(self) -> None: ...
    def fetch_metadata(self) -> dict[str, Any]:
        return {}


@pytest.fixture(autouse=True)
def _clean_registry():
    """Snapshot and restore the registry around each test."""
    original = dict(PROVIDER_REGISTRY)
    yield
    PROVIDER_REGISTRY.clear()
    PROVIDER_REGISTRY.update(original)


class TestGetProvider:
    """Tests for get_provider lookup and instantiation."""

    def test_get_provider_with_known_id_returns_instance(self):
        provider = get_provider("mock", records=[{"a": "1"}])
        assert isinstance(provider, MockDataProvider)

    def test_get_provider_with_unknown_id_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown provider: nonexistent"):
            get_provider("nonexistent")

    def test_get_provider_passes_kwargs_to_constructor(self):
        records = [{"x": "y"}]
        provider = get_provider("mock", records=records)
        assert isinstance(provider, MockDataProvider)
        result = list(provider.stream_records())
        assert result == records


class TestRegisterProvider:
    """Tests for register_provider."""

    def test_register_new_provider_succeeds(self):
        register_provider("dummy", _DummyProvider)
        assert "dummy" in PROVIDER_REGISTRY
        assert PROVIDER_REGISTRY["dummy"] is _DummyProvider

    def test_register_duplicate_id_raises_value_error(self):
        register_provider("dummy", _DummyProvider)
        with pytest.raises(ValueError, match="Provider already registered: dummy"):
            register_provider("dummy", _DummyProvider)

    def test_registered_provider_is_retrievable_via_get_provider(self):
        register_provider("dummy", _DummyProvider)
        provider = get_provider("dummy")
        assert isinstance(provider, _DummyProvider)


class TestListProviders:
    """Tests for list_providers."""

    def test_list_providers_includes_mock(self):
        providers = list_providers()
        assert "mock" in providers

    def test_list_providers_returns_sorted_list(self):
        register_provider("zzz_provider", _DummyProvider)
        register_provider("aaa_provider", _DummyProvider)
        providers = list_providers()
        assert providers == sorted(providers)
