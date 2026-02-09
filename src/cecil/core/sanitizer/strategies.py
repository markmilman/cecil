"""Redaction strategy interface.

Defines the abstract base class that all sanitization strategies
must implement to participate in the Cecil sanitization pipeline.
"""

from __future__ import annotations

import abc
import logging
from typing import Any

from cecil.core.sanitizer.models import Detection


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
