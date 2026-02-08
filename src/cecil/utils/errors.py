"""Cecil error hierarchy.

Defines the base exception and domain-specific error classes used
throughout the Cecil pipeline stages.
"""

from __future__ import annotations


class CecilError(Exception):
    """Base exception for all Cecil errors."""


# ── Ingestion stage ────────────────────────────────────────────────────


class IngestionError(CecilError):
    """Errors during data ingestion (providers)."""


class ProviderConnectionError(IngestionError):
    """Cannot connect to data source."""


class ProviderReadError(IngestionError):
    """Error reading records from data source."""


class ProviderDependencyError(IngestionError):
    """A required third-party dependency for a provider is missing."""


# ── Sanitization stage ─────────────────────────────────────────────────


class SanitizationError(CecilError):
    """Errors during PII detection or redaction."""


# ── Output stage ───────────────────────────────────────────────────────


class OutputError(CecilError):
    """Errors writing sanitized output."""


# ── Telemetry stage ────────────────────────────────────────────────────


class TelemetryError(CecilError):
    """Errors during SaaS metadata push."""


class TelemetryBlockedError(TelemetryError):
    """Telemetry was blocked by policy (e.g., Audit mode or PII detected)."""


# ── IPC / Server stage ────────────────────────────────────────────────


class ServerError(CecilError):
    """Errors related to the local IPC server."""


class ServerStartupError(ServerError):
    """The FastAPI/Uvicorn server failed to start or become ready."""
