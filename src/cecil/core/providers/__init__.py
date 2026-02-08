"""Data ingestion providers for the Cecil Safe-Pipe."""

from __future__ import annotations

from cecil.core.providers.base import BaseDataProvider
from cecil.core.providers.local_file import LocalFileProvider
from cecil.core.providers.mock import MockDataProvider
from cecil.core.providers.registry import get_provider, list_providers, register_provider


__all__ = [
    "BaseDataProvider",
    "LocalFileProvider",
    "MockDataProvider",
    "get_provider",
    "list_providers",
    "register_provider",
]
