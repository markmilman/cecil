"""Cecil utility modules."""

from __future__ import annotations

from cecil.utils.errors import (
    CecilError,
    IngestionError,
    OutputError,
    ProviderConnectionError,
    ProviderDependencyError,
    ProviderReadError,
    SanitizationError,
    ServerError,
    ServerStartupError,
    TelemetryBlockedError,
    TelemetryError,
)
from cecil.utils.paths import get_base_path, get_resource_path, get_ui_dist_path, is_frozen


__all__ = [
    "CecilError",
    "IngestionError",
    "OutputError",
    "ProviderConnectionError",
    "ProviderDependencyError",
    "ProviderReadError",
    "SanitizationError",
    "ServerError",
    "ServerStartupError",
    "TelemetryBlockedError",
    "TelemetryError",
    "get_base_path",
    "get_resource_path",
    "get_ui_dist_path",
    "is_frozen",
]
