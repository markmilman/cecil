"""Redaction strategy interface and built-in implementations.

Defines the abstract base class that all sanitization strategies
must implement to participate in the Cecil sanitization pipeline,
along with the ``StrictStrategy`` concrete implementation for
field-level redaction based on a ``FieldMapping`` configuration.
"""

from __future__ import annotations

import abc
import hashlib
import logging
from typing import Any

from cecil.core.sanitizer.models import Detection, FieldMapping, RedactionAction


logger = logging.getLogger(__name__)


class RedactionStrategy(abc.ABC):
    """Abstract base for detecting and redacting sensitive data.

    Concrete implementations define the rules for identifying PII/PHI
    within field values and replacing detected spans with safe
    placeholders.  The two primary strategies are:

    * **StrictStrategy** -- keeps only explicitly mapped fields;
      redacts everything else.
    * **DeepInterceptorStrategy** -- recursively inspects nested
      structures for sensitive key patterns using Presidio and
      custom regex recognizers.

    Strategies are injected into the ``SanitizationEngine`` via
    dependency injection, allowing the engine to remain agnostic
    about the detection and redaction logic.
    """

    @abc.abstractmethod
    def scan_value(self, key: str, value: Any) -> list[Detection]:
        """Scan a single field value for sensitive data.

        Examines the given value (typically a string, but
        implementations may handle other types) and returns a list
        of detected sensitive spans.

        Args:
            key: The field name associated with the value, which
                may influence detection heuristics (e.g., a field
                named ``"email"`` warrants stricter scanning).
            value: The field value to scan for PII/PHI.

        Returns:
            A list of ``Detection`` instances describing each
            sensitive span found within the value.  Returns an
            empty list if no sensitive data is detected.
        """

    @abc.abstractmethod
    def redact(self, value: str, detections: list[Detection]) -> str:
        """Replace detected sensitive spans with safe placeholders.

        Applies redaction to the original string value by replacing
        each detected span with an appropriate placeholder token
        (e.g., ``[EMAIL_REDACTED]``, ``[SSN_REDACTED]``).

        Detections are processed in reverse offset order so that
        earlier offsets remain valid after later replacements.

        Args:
            value: The original string value containing sensitive
                data.
            detections: The list of ``Detection`` instances
                identifying sensitive spans within the value.

        Returns:
            The redacted string with all detected spans replaced
            by their corresponding placeholders.
        """


class StrictStrategy(RedactionStrategy):
    """Field-level redaction strategy driven by a ``FieldMapping``.

    The StrictStrategy applies a per-field action based on an explicit
    mapping configuration.  Fields not present in the mapping default
    to ``REDACT`` (safe by default).

    Supported actions:

    * **KEEP** -- pass the value through unchanged.
    * **REDACT** -- replace the entire value with a
      ``[FIELD_NAME_REDACTED]`` placeholder.
    * **MASK** -- partially hide the value.  For emails, show the
      first character of the local part plus ``***@domain``.  For
      other strings longer than 4 characters, show the first and
      last characters with ``***`` between them.  Short strings
      are replaced with ``***``.
    * **HASH** -- replace with a deterministic ``hash_`` prefix
      followed by the first 16 hex characters of the SHA-256 digest.

    Args:
        mapping: A ``FieldMapping`` that assigns a ``RedactionAction``
            to each known field name.

    Attributes:
        mapping: The field mapping used to determine per-field actions.
    """

    def __init__(self, mapping: FieldMapping) -> None:
        self.mapping: FieldMapping = mapping
        self._last_key: str = ""

    def scan_value(self, key: str, value: Any) -> list[Detection]:
        """Scan a field value and return detections based on the mapping.

        Looks up the field ``key`` in the mapping to determine the
        redaction action.  If the action is ``KEEP``, returns an empty
        list.  For all other actions (``REDACT``, ``MASK``, ``HASH``),
        returns a single ``Detection`` covering the full string
        representation of the value.

        Non-string values are converted to ``str`` before measuring
        the span length.  Unmapped fields default to ``REDACT``.

        Args:
            key: The field name to look up in the mapping.
            value: The field value to scan.  Non-string values are
                converted to ``str``.

        Returns:
            A list containing zero or one ``Detection`` instances.
        """
        self._last_key = key

        action = self.mapping.get(key, RedactionAction.REDACT)
        if action is None:
            action = RedactionAction.REDACT

        if action is RedactionAction.KEEP:
            return []

        str_value = str(value) if not isinstance(value, str) else value

        logger.debug(
            "strict_scan key=%s action=%s value_len=%d",
            key,
            action.name,
            len(str_value),
        )

        return [
            Detection(
                entity_type=action.name,
                start=0,
                end=len(str_value),
                score=1.0,
            ),
        ]

    def redact(self, value: str, detections: list[Detection]) -> str:
        """Apply the redaction action encoded in the detection.

        If no detections are provided (i.e., the field was ``KEEP``),
        the original value is returned unchanged.

        For each detection, the ``entity_type`` field determines the
        action to apply:

        * ``"REDACT"`` -- replaces with ``[KEY_REDACTED]``
        * ``"MASK"`` -- partially hides the value
        * ``"HASH"`` -- produces a deterministic hash

        Args:
            value: The original string value.
            detections: Detections from a prior ``scan_value`` call.

        Returns:
            The redacted string value.
        """
        if not detections:
            return value

        detection = detections[0]
        action_name = detection.entity_type

        if action_name == RedactionAction.REDACT.name:
            return self._apply_redact(value)
        if action_name == RedactionAction.MASK.name:
            return self._apply_mask(value)
        if action_name == RedactionAction.HASH.name:
            return self._apply_hash(value)

        return value

    # -- Private helpers -----------------------------------------------------

    def _apply_redact(self, value: str) -> str:
        """Replace value with ``[KEY_REDACTED]`` placeholder.

        Args:
            value: The original value (unused, fully replaced).

        Returns:
            A placeholder string like ``[EMAIL_REDACTED]``.
        """
        placeholder_key = self._last_key.upper()
        return f"[{placeholder_key}_REDACTED]"

    @staticmethod
    def _apply_mask(value: str) -> str:
        """Partially hide a string value.

        For email addresses (detected by the presence of ``@``),
        shows the first character of the local part, ``***``, and
        the full domain.  For other strings longer than 4 characters,
        shows the first and last characters with ``***`` between them.
        Short strings (4 chars or fewer) are replaced with ``***``.

        Args:
            value: The string to mask.

        Returns:
            The masked string.
        """
        if "@" in value:
            local, domain = value.split("@", 1)
            return f"{local[0]}***@{domain}"

        if len(value) > 4:
            return f"{value[0]}***{value[-1]}"

        return "***"

    @staticmethod
    def _apply_hash(value: str) -> str:
        """Produce a deterministic, truncated SHA-256 hash.

        Args:
            value: The string to hash.

        Returns:
            A string like ``hash_<first-16-hex-chars>``.
        """
        digest = hashlib.sha256(value.encode()).hexdigest()[:16]
        return f"hash_{digest}"
