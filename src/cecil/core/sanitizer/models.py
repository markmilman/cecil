"""Sanitization domain models and types.

Defines the core data structures used throughout the sanitization
pipeline: redaction actions, field mappings, detection results,
audit records, and error-handling policies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class RedactionAction(Enum):
    """Actions that can be applied to a field during sanitization.

    Each action defines how a field value is transformed in the
    sanitized output.  Actions are assigned per-field via a
    ``FieldMapping``.
    """

    REDACT = "redact"
    """Remove the value entirely, replacing it with a placeholder."""

    MASK = "mask"
    """Partially hide the value (e.g., ``j***@example.com``)."""

    HASH = "hash"
    """Replace with a deterministic, irreversible hash for consistent anonymization."""

    KEEP = "keep"
    """Pass the value through without modification."""


class StreamErrorPolicy(Enum):
    """Controls behaviour when individual records fail during streaming.

    Used by the ``SanitizationEngine`` to decide whether to skip
    failed records or abort the entire stream.
    """

    SKIP_RECORD = "skip_record"
    """Log the error and continue processing the next record."""

    ABORT_STREAM = "abort_stream"
    """Raise immediately and halt the pipeline."""


@dataclass(frozen=True)
class Detection:
    """A single PII/PHI detection within a field value.

    Represents a span of text identified as potentially sensitive
    by a ``RedactionStrategy``.

    Attributes:
        entity_type: The type of entity detected (e.g., ``"EMAIL"``,
            ``"SSN"``, ``"API_KEY"``).
        start: The start character offset of the detection within
            the scanned value.
        end: The end character offset (exclusive) of the detection
            within the scanned value.
        score: A confidence score between 0.0 and 1.0 indicating
            how likely the span is to be the declared entity type.
    """

    entity_type: str
    start: int
    end: int
    score: float


@dataclass(frozen=True)
class FieldRedaction:
    """Audit record for a single field that was redacted.

    Attributes:
        field_name: The key of the field in the source record.
        action: The redaction action that was applied.
        entity_type: The type of entity that triggered the redaction.
        count: The number of detections of this entity type found
            in the field value.
    """

    field_name: str
    action: RedactionAction
    entity_type: str
    count: int


@dataclass(frozen=True)
class RedactionAudit:
    """Audit trail for the sanitization of a single record.

    Every record processed by the sanitization engine produces a
    ``RedactionAudit`` that documents which fields were modified
    and why.  This is displayed in the UI Audit View and stored
    locally alongside the sanitized output.

    Attributes:
        record_id: A unique identifier for the source record.
        fields_redacted: Details of each field that was redacted.
        timestamp: The UTC time at which the redaction was performed.
    """

    record_id: str
    fields_redacted: list[FieldRedaction]
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )


@dataclass(frozen=True)
class SanitizedRecord:
    """A sanitized data record paired with its redaction audit.

    This is the output unit of the sanitization pipeline.  The
    ``data`` dictionary contains the cleaned record (with PII
    replaced by placeholders), and the ``audit`` holds the
    corresponding audit trail.

    Attributes:
        data: The sanitized key-value record.
        audit: The redaction audit documenting what was changed.
    """

    data: dict[str, Any]
    audit: RedactionAudit


class FieldMapping:
    """Maps field names to their assigned redaction actions.

    Provides a dict-like interface for looking up the
    ``RedactionAction`` associated with a given field name.

    Args:
        mappings: A dictionary mapping field names to their
            ``RedactionAction`` values.
    """

    def __init__(self, mappings: dict[str, RedactionAction] | None = None) -> None:
        self._mappings: dict[str, RedactionAction] = dict(mappings) if mappings else {}

    def __getitem__(self, key: str) -> RedactionAction:
        """Return the redaction action for the given field name.

        Args:
            key: The field name to look up.

        Returns:
            The ``RedactionAction`` assigned to the field.

        Raises:
            KeyError: If the field name is not in the mapping.
        """
        return self._mappings[key]

    def __contains__(self, key: object) -> bool:
        """Check whether a field name is present in the mapping.

        Args:
            key: The field name to check.

        Returns:
            ``True`` if the field is mapped, ``False`` otherwise.
        """
        return key in self._mappings

    def __len__(self) -> int:
        """Return the number of mapped fields."""
        return len(self._mappings)

    def __iter__(self) -> Any:
        """Iterate over the mapped field names."""
        return iter(self._mappings)

    def get(self, key: str, default: RedactionAction | None = None) -> RedactionAction | None:
        """Return the action for a field, or a default if not mapped.

        Args:
            key: The field name to look up.
            default: The value to return if the key is absent.

        Returns:
            The ``RedactionAction`` for the field, or *default*.
        """
        return self._mappings.get(key, default)

    def items(self) -> Any:
        """Return a view of (field_name, action) pairs."""
        return self._mappings.items()

    def keys(self) -> Any:
        """Return a view of the mapped field names."""
        return self._mappings.keys()

    def values(self) -> Any:
        """Return a view of the mapped redaction actions."""
        return self._mappings.values()

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"FieldMapping({self._mappings!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another FieldMapping."""
        if not isinstance(other, FieldMapping):
            return NotImplemented
        return self._mappings == other._mappings
