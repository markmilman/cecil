"""Redaction strategy interface and built-in implementations.

Defines the abstract base class that all sanitization strategies
must implement to participate in the Cecil sanitization pipeline,
along with the ``StrictStrategy`` and ``DeepInterceptorStrategy``
concrete implementations.
"""

from __future__ import annotations

import abc
import hashlib
import json
import logging
import re
from typing import Any

from cecil.core.sanitizer.models import Detection, FieldMapping, RedactionAction


logger = logging.getLogger(__name__)


# -- Sensitive key pattern ---------------------------------------------------

_SENSITIVE_KEY_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(api[_-]?key|secret|password|passwd|token|auth|credential"
    r"|ssn|social.?security)",
)

# -- Custom regex patterns ---------------------------------------------------

_AWS_ACCESS_KEY_PATTERN: re.Pattern[str] = re.compile(
    r"(?:AKIA|ASIA)[A-Z0-9]{16}",
)

# -- Presidio entity types to detect ----------------------------------------

_PRESIDIO_ENTITIES: list[str] = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "PERSON",
    "IP_ADDRESS",
    "US_BANK_NUMBER",
    "IBAN_CODE",
    "MEDICAL_LICENSE",
    "URL",
]


def _create_presidio_analyzer() -> Any:
    """Create and return a Presidio ``AnalyzerEngine``.

    Isolated into a module-level function so it can be patched in
    tests to simulate unavailability.

    Returns:
        A Presidio ``AnalyzerEngine`` instance.

    Raises:
        ImportError: If ``presidio_analyzer`` is not installed or the
            required spaCy model is missing.
    """
    from presidio_analyzer import AnalyzerEngine

    return AnalyzerEngine()


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


class DeepInterceptorStrategy(RedactionStrategy):
    """Recursive PII detection strategy using Presidio and custom regex.

    The DeepInterceptorStrategy combines Microsoft Presidio NLP-based
    entity recognition with custom regex patterns to detect sensitive
    data within field values.  It supports:

    * **Sensitive key detection** -- field names matching patterns
      like ``api_key``, ``secret``, ``password``, etc. trigger
      full-value redaction.
    * **Presidio NLP detection** -- emails, phone numbers, credit
      cards, IP addresses, SSNs, and other PII entities.
    * **Custom regex** -- AWS access keys (``AKIA``/``ASIA`` prefix).
    * **Nested structures** -- dict and list values are serialized
      to JSON and scanned; JSON-encoded strings are parsed first.

    The Presidio ``AnalyzerEngine`` is created lazily on the first
    call to ``scan_value`` to avoid import-time overhead.  If Presidio
    or the required spaCy model is unavailable, the strategy falls
    back to regex-only detection and logs a warning.
    """

    def __init__(self) -> None:
        self._analyzer: Any = None
        self._analyzer_initialized: bool = False

    def _ensure_analyzer(self) -> None:
        """Lazily initialize the Presidio analyzer on first use.

        If Presidio or the spaCy NLP model is not available, sets
        the analyzer to ``None`` and logs a warning.  Subsequent
        calls are no-ops once initialization has been attempted.
        """
        if self._analyzer_initialized:
            return

        self._analyzer_initialized = True
        try:
            self._analyzer = _create_presidio_analyzer()
        except (ImportError, OSError) as exc:
            logger.warning(
                "Presidio analyzer unavailable, falling back to regex-only detection: %s",
                type(exc).__name__,
            )
            self._analyzer = None

    def scan_value(self, key: str, value: Any) -> list[Detection]:
        """Scan a field value for sensitive data using Presidio and regex.

        Detection pipeline:

        1. Check if the key name matches sensitive patterns; if so,
           return a ``SENSITIVE_KEY`` detection covering the full value.
        2. Convert non-string values (dict, list, or JSON strings)
           to a scannable string representation.
        3. Run Presidio entity detection (if available).
        4. Run custom regex patterns (AWS access keys).
        5. Deduplicate overlapping detections, preferring higher scores.

        Args:
            key: The field name associated with the value.
            value: The field value to scan.  Accepts strings, numbers,
                booleans, dicts, lists, and ``None``.

        Returns:
            A list of ``Detection`` instances.  Empty if no sensitive
            data is found.
        """
        if value is None:
            return []

        self._ensure_analyzer()

        # Convert value to string for scanning.
        str_value = self._to_scannable_string(value)

        detections: list[Detection] = []

        # 1. Sensitive key detection.
        if _SENSITIVE_KEY_PATTERN.search(key):
            detections.append(
                Detection(
                    entity_type="SENSITIVE_KEY",
                    start=0,
                    end=len(str_value),
                    score=1.0,
                ),
            )
            logger.debug(
                "deep_scan sensitive_key=%s value_len=%d",
                key,
                len(str_value),
            )
            return detections

        # 2. Presidio detection.
        if self._analyzer is not None:
            detections.extend(self._run_presidio(str_value))

        # 3. Custom regex patterns.
        detections.extend(self._run_custom_regex(str_value))

        # 4. Deduplicate overlapping detections.
        detections = self._deduplicate(detections)

        if detections:
            logger.debug(
                "deep_scan key=%s detection_count=%d value_len=%d",
                key,
                len(detections),
                len(str_value),
            )

        return detections

    def redact(self, value: str, detections: list[Detection]) -> str:
        """Replace detected spans with ``[ENTITY_TYPE_REDACTED]`` placeholders.

        Detections are sorted by start position in descending order
        so that replacements do not shift the offsets of earlier
        detections.

        For ``SENSITIVE_KEY`` detections, the entire value is replaced
        regardless of span offsets.

        Args:
            value: The original string value.
            detections: Detections from a prior ``scan_value`` call.

        Returns:
            The redacted string with placeholders substituted.
        """
        if not detections:
            return value

        # Check for SENSITIVE_KEY -- replace entire value.
        for det in detections:
            if det.entity_type == "SENSITIVE_KEY":
                return "[SENSITIVE_KEY_REDACTED]"

        # Sort by start position descending to preserve offsets.
        sorted_detections = sorted(
            detections,
            key=lambda det: det.start,
            reverse=True,
        )

        result = value
        for det in sorted_detections:
            placeholder = f"[{det.entity_type}_REDACTED]"
            result = result[: det.start] + placeholder + result[det.end :]

        return result

    # -- Private helpers -----------------------------------------------------

    @staticmethod
    def _to_scannable_string(value: Any) -> str:
        """Convert a value to a string suitable for scanning.

        Handles dict, list, and JSON-encoded string values by
        serializing or parsing them appropriately.

        Args:
            value: The value to convert.

        Returns:
            A string representation of the value.
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str)

        str_value = str(value) if not isinstance(value, str) else value

        # Try to parse JSON strings for scanning.
        if str_value and str_value[0] in ("{", "["):
            try:
                parsed = json.loads(str_value)
                if isinstance(parsed, (dict, list)):
                    return json.dumps(parsed, default=str)
            except (json.JSONDecodeError, ValueError):
                pass

        return str_value

    def _run_presidio(self, text: str) -> list[Detection]:
        """Run Presidio entity detection on the given text.

        Args:
            text: The text to analyze.

        Returns:
            A list of ``Detection`` instances from Presidio results.
        """
        if not text or self._analyzer is None:
            return []

        results = self._analyzer.analyze(
            text=text,
            language="en",
            entities=_PRESIDIO_ENTITIES,
        )

        return [
            Detection(
                entity_type=r.entity_type,
                start=r.start,
                end=r.end,
                score=float(r.score),
            )
            for r in results
        ]

    @staticmethod
    def _run_custom_regex(text: str) -> list[Detection]:
        """Run custom regex patterns on the given text.

        Currently detects:
        * AWS access keys (``AKIA`` or ``ASIA`` prefix + 16 chars).

        Args:
            text: The text to scan.

        Returns:
            A list of ``Detection`` instances from regex matches.
        """
        detections: list[Detection] = []

        for match in _AWS_ACCESS_KEY_PATTERN.finditer(text):
            detections.append(
                Detection(
                    entity_type="AWS_ACCESS_KEY",
                    start=match.start(),
                    end=match.end(),
                    score=0.9,
                ),
            )

        return detections

    @staticmethod
    def _deduplicate(detections: list[Detection]) -> list[Detection]:
        """Remove overlapping detections, keeping higher-scored ones.

        When two detections overlap, the one with the higher score is
        retained.  Ties are broken by preferring the longer span.

        Args:
            detections: The raw list of detections.

        Returns:
            A deduplicated list of non-overlapping detections.
        """
        if len(detections) <= 1:
            return detections

        # Sort by start position, then by score descending.
        sorted_dets = sorted(
            detections,
            key=lambda det: (det.start, -det.score, -(det.end - det.start)),
        )

        result: list[Detection] = []
        for det in sorted_dets:
            # Check if this detection overlaps with the last kept one.
            if result and det.start < result[-1].end:
                # Keep the one with higher score or longer span.
                prev = result[-1]
                if det.score > prev.score or (
                    det.score == prev.score and (det.end - det.start) > (prev.end - prev.start)
                ):
                    result[-1] = det
                continue
            result.append(det)

        return result
