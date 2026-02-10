"""Field-level redaction action executors.

Provides standalone functions for each ``RedactionAction`` and an
``apply_action`` dispatcher that routes to the correct executor
based on the action enum value.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from cecil.core.sanitizer.models import RedactionAction


logger = logging.getLogger(__name__)


def apply_redact(value: str, field_name: str) -> str:
    """Replace a value with a field-specific redaction placeholder.

    Returns a placeholder string in the form ``[FIELD_NAME_REDACTED]``,
    where the field name is upper-cased.

    Args:
        value: The original value (unused; fully replaced).
        field_name: The field name to embed in the placeholder.

    Returns:
        A placeholder string such as ``[USER_EMAIL_REDACTED]``.
    """
    return f"[{field_name.upper()}_REDACTED]"


def apply_mask(value: str, *, preserve_domain: bool = False) -> str:
    """Partially hide a string value.

    For email addresses (detected by the presence of ``@``):

    * Shows the first character of the local part, ``***``, and
      the full domain (e.g., ``j***@example.com``).

    For non-email strings longer than 4 characters:

    * Shows the first and last characters with ``***`` between them
      (e.g., ``p***3``).

    For strings of 4 characters or fewer (including empty strings):

    * Returns ``"***"``.

    Args:
        value: The string to mask.
        preserve_domain: Accepted for forward-compatibility but
            currently has no additional effect beyond the default
            email masking behaviour.

    Returns:
        The masked string.
    """
    if "@" in value:
        local, domain = value.split("@", 1)
        first_char = local[0] if local else ""
        return f"{first_char}***@{domain}"

    if len(value) > 4:
        return f"{value[0]}***{value[-1]}"

    return "***"


def apply_hash(value: str) -> str:
    """Produce a deterministic, truncated SHA-256 hash of a value.

    The hash is computed from the UTF-8 encoding of *value* and
    truncated to the first 16 hexadecimal characters.

    Args:
        value: The string to hash.

    Returns:
        A string in the form ``hash_<first-16-hex-chars>``.
    """
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"hash_{digest}"


def apply_keep(value: str) -> str:
    """Return the value unchanged.

    This is the identity action -- the value passes through
    without any modification.

    Args:
        value: The string to keep.

    Returns:
        The original *value*, unmodified.
    """
    return value


def apply_action(
    value: str,
    action: RedactionAction,
    field_name: str = "",
    *,
    options: dict[str, Any] | None = None,
) -> str:
    """Dispatch to the correct action executor based on *action*.

    Routes to one of ``apply_redact``, ``apply_mask``, ``apply_hash``,
    or ``apply_keep`` depending on the ``RedactionAction`` enum value.

    Args:
        value: The string to transform.
        action: The ``RedactionAction`` that determines which executor
            is invoked.
        field_name: The field name, passed to ``apply_redact`` when
            the action is ``REDACT``.
        options: Optional action-specific parameters.  Currently
            recognised keys:

            * ``preserve_domain`` (bool) -- forwarded to
              ``apply_mask`` when the action is ``MASK``.

    Returns:
        The transformed string produced by the selected executor.
    """
    logger.debug(
        "apply_action field=%s action=%s value_len=%d",
        field_name,
        action.name,
        len(value),
    )

    if action is RedactionAction.REDACT:
        return apply_redact(value, field_name)

    if action is RedactionAction.MASK:
        preserve_domain = False
        if options is not None:
            preserve_domain = bool(options.get("preserve_domain", False))
        return apply_mask(value, preserve_domain=preserve_domain)

    if action is RedactionAction.HASH:
        return apply_hash(value)

    # KEEP
    return apply_keep(value)
