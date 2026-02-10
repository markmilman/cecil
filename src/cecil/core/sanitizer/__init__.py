"""Sanitization engine and strategies for the Cecil Safe-Pipe."""

from __future__ import annotations

from cecil.core.sanitizer.actions import (
    apply_action,
    apply_hash,
    apply_keep,
    apply_mask,
    apply_redact,
)
from cecil.core.sanitizer.engine import SanitizationEngine
from cecil.core.sanitizer.mapping import MappingParser
from cecil.core.sanitizer.models import (
    Detection,
    FieldMapping,
    FieldMappingEntry,
    FieldRedaction,
    MappingConfig,
    MappingValidationResult,
    RedactionAction,
    RedactionAudit,
    SanitizedRecord,
    StreamErrorPolicy,
)
from cecil.core.sanitizer.strategies import (
    DeepInterceptorStrategy,
    RedactionStrategy,
    StrictStrategy,
)


__all__ = [
    "DeepInterceptorStrategy",
    "Detection",
    "FieldMapping",
    "FieldMappingEntry",
    "FieldRedaction",
    "MappingConfig",
    "MappingParser",
    "MappingValidationResult",
    "RedactionAction",
    "RedactionAudit",
    "RedactionStrategy",
    "SanitizationEngine",
    "SanitizedRecord",
    "StreamErrorPolicy",
    "StrictStrategy",
    "apply_action",
    "apply_hash",
    "apply_keep",
    "apply_mask",
    "apply_redact",
]
