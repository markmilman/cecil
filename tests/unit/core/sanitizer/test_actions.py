"""Tests for field-level redaction action executors.

Covers all individual action functions (``apply_redact``, ``apply_mask``,
``apply_hash``, ``apply_keep``) and the ``apply_action`` dispatcher,
including edge cases for empty strings, short strings, and option handling.
"""

from __future__ import annotations

import hashlib

from cecil.core.sanitizer.actions import (
    apply_action,
    apply_hash,
    apply_keep,
    apply_mask,
    apply_redact,
)
from cecil.core.sanitizer.models import RedactionAction


# -- apply_redact ------------------------------------------------------------


class TestApplyRedact:
    """Tests for the apply_redact function."""

    def test_apply_redact_returns_placeholder_with_field_name(self) -> None:
        result = apply_redact("john@example.com", "user_email")
        assert result == "[USER_EMAIL_REDACTED]"

    def test_apply_redact_uppercases_field_name(self) -> None:
        result = apply_redact("secret", "api_key")
        assert result == "[API_KEY_REDACTED]"
        assert "api_key" not in result

    def test_apply_redact_empty_value_still_returns_placeholder(self) -> None:
        result = apply_redact("", "email")
        assert result == "[EMAIL_REDACTED]"


# -- apply_mask --------------------------------------------------------------


class TestApplyMask:
    """Tests for the apply_mask function."""

    def test_apply_mask_email_shows_first_char_and_domain(self) -> None:
        result = apply_mask("john@example.com")
        assert result == "j***@example.com"

    def test_apply_mask_email_preserves_domain_flag(self) -> None:
        result = apply_mask("john@example.com", preserve_domain=True)
        assert result == "j***@example.com"

    def test_apply_mask_long_string_shows_first_and_last(self) -> None:
        result = apply_mask("password123")
        assert result == "p***3"

    def test_apply_mask_short_string_returns_stars(self) -> None:
        result = apply_mask("abc")
        assert result == "***"

    def test_apply_mask_empty_string_returns_stars(self) -> None:
        result = apply_mask("")
        assert result == "***"

    def test_apply_mask_exact_four_chars_returns_stars(self) -> None:
        result = apply_mask("abcd")
        assert result == "***"

    def test_apply_mask_five_chars_shows_first_and_last(self) -> None:
        result = apply_mask("abcde")
        assert result == "a***e"


# -- apply_hash --------------------------------------------------------------


class TestApplyHash:
    """Tests for the apply_hash function."""

    def test_apply_hash_returns_hash_prefix(self) -> None:
        result = apply_hash("john@example.com")
        assert result.startswith("hash_")
        # prefix + 16 hex chars
        assert len(result) == 5 + 16

    def test_apply_hash_deterministic_same_input(self) -> None:
        result1 = apply_hash("john@example.com")
        result2 = apply_hash("john@example.com")
        assert result1 == result2

    def test_apply_hash_different_inputs_differ(self) -> None:
        result1 = apply_hash("alice@example.com")
        result2 = apply_hash("bob@example.com")
        assert result1 != result2

    def test_apply_hash_does_not_contain_original_value(self) -> None:
        value = "john@example.com"
        result = apply_hash(value)
        assert value not in result
        assert "john" not in result

    def test_apply_hash_empty_string_still_hashes(self) -> None:
        result = apply_hash("")
        expected = hashlib.sha256(b"").hexdigest()[:16]
        assert result == f"hash_{expected}"


# -- apply_keep --------------------------------------------------------------


class TestApplyKeep:
    """Tests for the apply_keep function."""

    def test_apply_keep_returns_unchanged(self) -> None:
        result = apply_keep("gpt-4")
        assert result == "gpt-4"

    def test_apply_keep_empty_string_returns_empty(self) -> None:
        result = apply_keep("")
        assert result == ""


# -- apply_action dispatcher -------------------------------------------------


class TestApplyAction:
    """Tests for the apply_action dispatcher."""

    def test_apply_action_dispatches_redact(self) -> None:
        result = apply_action(
            "john@example.com",
            RedactionAction.REDACT,
            field_name="email",
        )
        assert result == "[EMAIL_REDACTED]"

    def test_apply_action_dispatches_mask(self) -> None:
        result = apply_action(
            "john@example.com",
            RedactionAction.MASK,
            field_name="email",
        )
        assert result == "j***@example.com"

    def test_apply_action_dispatches_hash(self) -> None:
        result = apply_action(
            "john@example.com",
            RedactionAction.HASH,
            field_name="email",
        )
        assert result.startswith("hash_")
        assert "john" not in result

    def test_apply_action_dispatches_keep(self) -> None:
        result = apply_action(
            "gpt-4",
            RedactionAction.KEEP,
            field_name="model",
        )
        assert result == "gpt-4"

    def test_apply_action_mask_with_options(self) -> None:
        result = apply_action(
            "john@example.com",
            RedactionAction.MASK,
            field_name="email",
            options={"preserve_domain": True},
        )
        assert result == "j***@example.com"

    def test_apply_action_mask_without_options(self) -> None:
        result = apply_action(
            "john@example.com",
            RedactionAction.MASK,
            field_name="email",
        )
        assert result == "j***@example.com"


# -- PII leak assertions for all action tests --------------------------------


class TestActionsPIILeakDetection:
    """Every action that transforms PII must not leak the original value."""

    def test_apply_redact_pii_absent_from_result(self) -> None:
        """apply_redact must not leak the original email."""
        pii = "john@example.com"
        result = apply_redact(pii, "user_email")
        assert pii not in result
        assert "john" not in result

    def test_apply_mask_email_pii_absent_from_result(self) -> None:
        """apply_mask for email must not leak the full local part."""
        pii = "john.doe@example.com"
        result = apply_mask(pii)
        assert "john.doe" not in result

    def test_apply_mask_string_pii_absent_from_result(self) -> None:
        """apply_mask for a long string must not leak the full original."""
        pii = "password123"
        result = apply_mask(pii)
        assert pii not in result

    def test_apply_hash_pii_absent_from_result(self) -> None:
        """apply_hash must not leak the original value."""
        pii = "123-45-6789"
        result = apply_hash(pii)
        assert pii not in result
        assert "123-45" not in result

    def test_apply_action_redact_pii_absent(self) -> None:
        """apply_action REDACT must not leak PII."""
        pii = "alice@corp.com"
        result = apply_action(pii, RedactionAction.REDACT, field_name="email")
        assert pii not in result
        assert "alice" not in result

    def test_apply_action_mask_pii_absent(self) -> None:
        """apply_action MASK must not leak PII."""
        pii = "bob.smith@corp.com"
        result = apply_action(pii, RedactionAction.MASK, field_name="email")
        assert "bob.smith" not in result

    def test_apply_action_hash_pii_absent(self) -> None:
        """apply_action HASH must not leak PII."""
        pii = "sk-secret-key-12345"
        result = apply_action(pii, RedactionAction.HASH, field_name="api_key")
        assert pii not in result
        assert "secret" not in result

    def test_apply_action_mask_with_preserve_domain_pii_absent(self) -> None:
        """apply_action MASK with preserve_domain must not leak local part."""
        pii = "sensitive.user@example.com"
        result = apply_action(
            pii,
            RedactionAction.MASK,
            field_name="email",
            options={"preserve_domain": True},
        )
        assert "sensitive.user" not in result

    def test_apply_mask_email_with_empty_local_part(self) -> None:
        """apply_mask handles edge case of @ at beginning."""
        result = apply_mask("@example.com")
        assert result == "***@example.com"

    def test_apply_mask_email_with_multiple_at_signs(self) -> None:
        """apply_mask splits on first @ only."""
        result = apply_mask("user@host@domain.com")
        assert result == "u***@host@domain.com"
        assert "user" not in result
