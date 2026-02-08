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
    TelemetryBlockedError,
    TelemetryError,
)


__all__ = [
    "CecilError",
    "IngestionError",
    "OutputError",
    "ProviderConnectionError",
    "ProviderDependencyError",
    "ProviderReadError",
    "SanitizationError",
    "TelemetryBlockedError",
    "TelemetryError",
]
