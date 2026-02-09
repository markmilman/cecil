"""SanitizationEngine — composes strategies with record streams.

The engine is the central orchestrator of the Cecil sanitization
pipeline.  It accepts a ``RedactionStrategy`` and processes a
stream of records, applying detection and redaction to each field,
producing ``SanitizedRecord`` instances with embedded audit trails.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Generator
from typing import Any

from cecil.core.sanitizer.models import (
    FieldRedaction,
    RedactionAction,
    RedactionAudit,
    SanitizedRecord,
    StreamErrorPolicy,
)
from cecil.core.sanitizer.strategies import RedactionStrategy
from cecil.utils.errors import RecordSanitizationError


logger = logging.getLogger(__name__)


class SanitizationEngine:
    """Composes a redaction strategy with provider record streams.

    The engine iterates over incoming records (as Python dicts),
    applies the configured ``RedactionStrategy`` to each field,
    and yields ``SanitizedRecord`` instances that pair the cleaned
    data with a ``RedactionAudit`` trail.

    Generator semantics are preserved end-to-end: records are
    processed one at a time with no buffering, respecting the
    50 MB resident-memory ceiling.

    Args:
        strategy: The redaction strategy to apply to each field.
        error_policy: How to handle per-record failures.
            Defaults to ``SKIP_RECORD``.

    Attributes:
        strategy: The active redaction strategy.
        error_policy: The active error-handling policy.
        records_processed: Total records seen by the engine.
        records_sanitized: Records successfully sanitized.
        records_failed: Records that raised errors.
        policy_hash: SHA-256 hex digest identifying the strategy
            configuration for audit verification.
    """

    def __init__(
        self,
        strategy: RedactionStrategy,
        error_policy: StreamErrorPolicy = StreamErrorPolicy.SKIP_RECORD,
    ) -> None:
        self.strategy: RedactionStrategy = strategy
        self.error_policy: StreamErrorPolicy = error_policy
        self.records_processed: int = 0
        self.records_sanitized: int = 0
        self.records_failed: int = 0
        self.policy_hash: str = self._compute_policy_hash()

    def reset_counters(self) -> None:
        """Reset all processing counters to zero."""
        self.records_processed = 0
        self.records_sanitized = 0
        self.records_failed = 0

    def process_stream(
        self,
        records: Generator[dict[str, Any], None, None],
    ) -> Generator[SanitizedRecord, None, None]:
        """Process a stream of records through the sanitization pipeline.

        For each record, every field is scanned for sensitive data
        using the configured strategy.  Detected fields are redacted,
        and an audit trail is generated.

        Args:
            records: A generator of raw data records (dicts).

        Yields:
            ``SanitizedRecord`` instances containing the cleaned data
            and the corresponding ``RedactionAudit``.

        Raises:
            RecordSanitizationError: If ``error_policy`` is
                ``ABORT_STREAM`` and a record fails processing.
        """
        for index, record in enumerate(records):
            self.records_processed += 1
            try:
                sanitized = self._process_record(record, index)
            except Exception as exc:
                self.records_failed += 1
                if self.error_policy is StreamErrorPolicy.ABORT_STREAM:
                    raise RecordSanitizationError(
                        f"Record sanitization failed at record_index={index}",
                    ) from exc
                logger.warning(
                    "Skipping failed record record_index=%d error=%s",
                    index,
                    type(exc).__name__,
                )
                continue
            self.records_sanitized += 1
            yield sanitized

    # -- Private helpers -----------------------------------------------------

    def _process_record(
        self,
        record: dict[str, Any],
        index: int,
    ) -> SanitizedRecord:
        """Sanitize a single record and build its audit trail.

        Args:
            record: The raw data record.
            index: The zero-based position in the stream.

        Returns:
            A ``SanitizedRecord`` with cleaned data and audit.
        """
        sanitized_data: dict[str, Any] = {}
        field_redactions: list[FieldRedaction] = []

        for key, value in record.items():
            detections = self.strategy.scan_value(key, value)

            if not detections:
                # No sensitive data found — keep original value.
                sanitized_data[key] = value
                continue

            # Redact the value.
            str_value = str(value) if not isinstance(value, str) else value
            redacted_value = self.strategy.redact(str_value, detections)
            sanitized_data[key] = redacted_value

            # Build the audit entry for this field.
            detection = detections[0]
            action = self._entity_type_to_action(detection.entity_type)
            field_redactions.append(
                FieldRedaction(
                    field_name=key,
                    action=action,
                    entity_type=detection.entity_type,
                    count=len(detections),
                ),
            )

        audit = RedactionAudit(
            record_id=str(index),
            fields_redacted=field_redactions,
        )

        return SanitizedRecord(data=sanitized_data, audit=audit)

    @staticmethod
    def _entity_type_to_action(entity_type: str) -> RedactionAction:
        """Map a detection entity type to a RedactionAction.

        For StrictStrategy detections the entity type is the action
        name itself (``"REDACT"``, ``"MASK"``, ``"HASH"``).  For
        DeepInterceptorStrategy detections the entity type is the
        PII category, which maps to ``REDACT``.

        Args:
            entity_type: The detection's entity type string.

        Returns:
            The corresponding ``RedactionAction``.
        """
        try:
            return RedactionAction[entity_type]
        except KeyError:
            return RedactionAction.REDACT

    def _compute_policy_hash(self) -> str:
        """Compute a SHA-256 hash identifying the strategy configuration.

        The hash includes the strategy class name and, for
        ``StrictStrategy``, the field mapping contents.  This
        allows SaaS verification that the same policy was applied.

        Returns:
            A 64-character hex digest string.
        """
        hasher = hashlib.sha256()
        hasher.update(type(self.strategy).__name__.encode())

        # Include mapping details for StrictStrategy.
        from cecil.core.sanitizer.strategies import StrictStrategy

        if isinstance(self.strategy, StrictStrategy):
            for key in sorted(self.strategy.mapping.keys()):
                action = self.strategy.mapping[key]
                hasher.update(f"{key}={action.value}".encode())

        return hasher.hexdigest()
