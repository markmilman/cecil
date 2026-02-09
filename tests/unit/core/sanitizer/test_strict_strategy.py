"""Tests for StrictStrategy field-level redaction.

Covers all redaction actions (KEEP, REDACT, MASK, HASH), unmapped field
defaults, non-string value handling, and PII leak detection.
"""

from __future__ import annotations

import hashlib

import pytest

from cecil.core.sanitizer.models import (
    FieldMapping,
    RedactionAction,
)
from cecil.core.sanitizer.strategies import StrictStrategy


# -- Fixtures ----------------------------------------------------------------


@pytest.fixture()
def simple_mapping() -> FieldMapping:
    """Return a mapping with one field per action type."""
    return FieldMapping(
        {
            "email": RedactionAction.REDACT,
            "name": RedactionAction.MASK,
            "user_id": RedactionAction.HASH,
            "model": RedactionAction.KEEP,
        }
    )


@pytest.fixture()
def strategy(simple_mapping: FieldMapping) -> StrictStrategy:
    """Return a StrictStrategy configured with the simple mapping."""
    return StrictStrategy(mapping=simple_mapping)


# -- Constructor -------------------------------------------------------------


class TestStrictStrategyInit:
    """Tests for StrictStrategy construction."""

    def test_init_accepts_field_mapping(self, simple_mapping: FieldMapping) -> None:
        strategy = StrictStrategy(mapping=simple_mapping)
        assert strategy is not None

    def test_init_stores_mapping(self, simple_mapping: FieldMapping) -> None:
        strategy = StrictStrategy(mapping=simple_mapping)
        assert strategy.mapping is simple_mapping


# -- scan_value: KEEP --------------------------------------------------------


class TestScanValueKeep:
    """scan_value returns empty list for KEEP fields."""

    def test_keep_field_returns_no_detections(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("model", "gpt-4")
        assert detections == []

    def test_keep_field_with_empty_string_returns_no_detections(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("model", "")
        assert detections == []


# -- scan_value: REDACT ------------------------------------------------------


class TestScanValueRedact:
    """scan_value returns a full-span Detection for REDACT fields."""

    def test_redact_field_returns_one_detection(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", "john@example.com")
        assert len(detections) == 1

    def test_redact_detection_covers_full_value(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "john@example.com"
        detections = strategy.scan_value("email", value)
        assert detections[0].start == 0
        assert detections[0].end == len(value)

    def test_redact_detection_entity_type_is_redact(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", "john@example.com")
        assert detections[0].entity_type == "REDACT"

    def test_redact_detection_score_is_one(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", "john@example.com")
        assert detections[0].score == 1.0


# -- scan_value: MASK --------------------------------------------------------


class TestScanValueMask:
    """scan_value returns a full-span Detection for MASK fields."""

    def test_mask_field_returns_one_detection(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("name", "John Doe")
        assert len(detections) == 1

    def test_mask_detection_entity_type_is_mask(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("name", "John Doe")
        assert detections[0].entity_type == "MASK"

    def test_mask_detection_covers_full_value(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "John Doe"
        detections = strategy.scan_value("name", value)
        assert detections[0].start == 0
        assert detections[0].end == len(value)


# -- scan_value: HASH -------------------------------------------------------


class TestScanValueHash:
    """scan_value returns a full-span Detection for HASH fields."""

    def test_hash_field_returns_one_detection(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("user_id", "uid-42")
        assert len(detections) == 1

    def test_hash_detection_entity_type_is_hash(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("user_id", "uid-42")
        assert detections[0].entity_type == "HASH"


# -- scan_value: unmapped fields ---------------------------------------------


class TestScanValueUnmapped:
    """Unmapped fields default to REDACT (safe by default)."""

    def test_unmapped_field_returns_redact_detection(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("secret_key", "sk-abc123")
        assert len(detections) == 1
        assert detections[0].entity_type == "REDACT"

    def test_unmapped_field_detection_covers_full_value(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "sk-abc123"
        detections = strategy.scan_value("secret_key", value)
        assert detections[0].start == 0
        assert detections[0].end == len(value)


# -- scan_value: non-string values -------------------------------------------


class TestScanValueNonString:
    """Non-string values are converted to str before scanning."""

    def test_integer_value_is_scanned_as_string(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", 12345)
        assert len(detections) == 1
        assert detections[0].end == len("12345")

    def test_none_value_is_scanned_as_string(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", None)
        assert len(detections) == 1
        assert detections[0].end == len("None")

    def test_float_value_is_scanned_as_string(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", 3.14)
        assert len(detections) == 1
        assert detections[0].end == len("3.14")

    def test_bool_value_is_scanned_as_string(
        self,
        strategy: StrictStrategy,
    ) -> None:
        detections = strategy.scan_value("email", True)
        assert len(detections) == 1
        assert detections[0].end == len("True")


# -- redact: REDACT action ---------------------------------------------------


class TestRedactActionRedact:
    """redact() replaces the full value with [FIELD_REDACTED] placeholder."""

    def test_redact_replaces_with_placeholder(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "john@example.com"
        detections = strategy.scan_value("email", value)
        result = strategy.redact(value, detections)
        assert result == "[EMAIL_REDACTED]"

    def test_redact_uses_uppercase_key_in_placeholder(
        self,
        strategy: StrictStrategy,
    ) -> None:
        mapping = FieldMapping({"api_key": RedactionAction.REDACT})
        s = StrictStrategy(mapping=mapping)
        value = "sk-secret123"
        detections = s.scan_value("api_key", value)
        result = s.redact(value, detections)
        assert result == "[API_KEY_REDACTED]"

    def test_redact_removes_original_pii(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "john@example.com"
        detections = strategy.scan_value("email", value)
        result = strategy.redact(value, detections)
        assert "john" not in result
        assert "example.com" not in result


# -- redact: MASK action for emails ------------------------------------------


class TestRedactActionMaskEmail:
    """MASK action for email-like values shows first char + *** + domain."""

    def test_mask_email_shows_first_char_and_domain(self) -> None:
        mapping = FieldMapping({"email": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "john@example.com"
        detections = s.scan_value("email", value)
        result = s.redact(value, detections)
        assert result == "j***@example.com"

    def test_mask_email_single_char_local_part(self) -> None:
        mapping = FieldMapping({"email": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "a@test.org"
        detections = s.scan_value("email", value)
        result = s.redact(value, detections)
        assert result == "a***@test.org"

    def test_mask_email_does_not_leak_full_local_part(self) -> None:
        mapping = FieldMapping({"email": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "john.doe@example.com"
        detections = s.scan_value("email", value)
        result = s.redact(value, detections)
        assert "john.doe" not in result
        assert result.startswith("j***@")


# -- redact: MASK action for non-emails --------------------------------------


class TestRedactActionMaskString:
    """MASK action for non-email strings."""

    def test_mask_long_string_shows_first_and_last_char(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "John Doe"
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result == "J***e"

    def test_mask_exactly_five_chars_shows_first_and_last(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "Alice"
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result == "A***e"

    def test_mask_four_char_string_is_replaced_with_stars(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "John"
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result == "***"

    def test_mask_short_string_is_replaced_with_stars(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "Jo"
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result == "***"

    def test_mask_single_char_is_replaced_with_stars(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "J"
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result == "***"

    def test_mask_empty_string_is_replaced_with_stars(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = ""
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result == "***"


# -- redact: HASH action -----------------------------------------------------


class TestRedactActionHash:
    """HASH action produces deterministic, prefixed hashes."""

    def test_hash_produces_prefixed_hash(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "uid-42"
        detections = strategy.scan_value("user_id", value)
        result = strategy.redact(value, detections)
        assert result.startswith("hash_")

    def test_hash_is_deterministic(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "uid-42"
        d1 = strategy.scan_value("user_id", value)
        result1 = strategy.redact(value, d1)
        d2 = strategy.scan_value("user_id", value)
        result2 = strategy.redact(value, d2)
        assert result1 == result2

    def test_hash_uses_sha256_truncated_to_16(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "uid-42"
        detections = strategy.scan_value("user_id", value)
        result = strategy.redact(value, detections)
        expected_hash = hashlib.sha256(value.encode()).hexdigest()[:16]
        assert result == f"hash_{expected_hash}"

    def test_hash_different_values_produce_different_hashes(
        self,
        strategy: StrictStrategy,
    ) -> None:
        d1 = strategy.scan_value("user_id", "uid-42")
        r1 = strategy.redact("uid-42", d1)
        d2 = strategy.scan_value("user_id", "uid-99")
        r2 = strategy.redact("uid-99", d2)
        assert r1 != r2

    def test_hash_does_not_leak_original_value(
        self,
        strategy: StrictStrategy,
    ) -> None:
        value = "uid-42"
        detections = strategy.scan_value("user_id", value)
        result = strategy.redact(value, detections)
        assert "uid-42" not in result


# -- redact: KEEP action (no detections) -------------------------------------


class TestRedactActionKeep:
    """KEEP action passes through value unchanged (no detections)."""

    def test_keep_returns_original_value(
        self,
        strategy: StrictStrategy,
    ) -> None:
        result = strategy.redact("gpt-4", [])
        assert result == "gpt-4"


# -- redact with empty detections -------------------------------------------


class TestRedactEmptyDetections:
    """redact() with no detections returns value unchanged."""

    def test_empty_detections_returns_original(
        self,
        strategy: StrictStrategy,
    ) -> None:
        result = strategy.redact("some value", [])
        assert result == "some value"


# -- Detection metadata fields -----------------------------------------------


class TestDetectionMetadata:
    """Detections carry the action name in entity_type."""

    def test_detection_from_scan_value_stores_action_in_entity_type(
        self,
        strategy: StrictStrategy,
    ) -> None:
        """The entity_type encodes the action. Verify the action name
        is stored in the Detection entity_type field."""
        detections = strategy.scan_value("email", "test@example.com")
        assert len(detections) == 1
        assert detections[0].entity_type == "REDACT"


# -- PII leak detection (safety-critical) ------------------------------------


class TestPIILeakDetection:
    """Verify that known PII values never appear in redacted output."""

    @pytest.mark.parametrize(
        ("field_name", "action", "pii_value"),
        [
            ("email", RedactionAction.REDACT, "john.doe@example.com"),
            ("ssn", RedactionAction.REDACT, "123-45-6789"),
            ("name", RedactionAction.MASK, "John Doe"),
            ("phone", RedactionAction.MASK, "(555) 867-5309"),
            ("api_key", RedactionAction.HASH, "sk-1234567890abcdef"),
        ],
    )
    def test_pii_not_present_in_redacted_output(
        self,
        field_name: str,
        action: RedactionAction,
        pii_value: str,
    ) -> None:
        mapping = FieldMapping({field_name: action})
        s = StrictStrategy(mapping=mapping)
        detections = s.scan_value(field_name, pii_value)
        result = s.redact(pii_value, detections)
        assert pii_value not in result

    def test_unmapped_field_pii_is_redacted(self) -> None:
        mapping = FieldMapping({})  # empty mapping
        s = StrictStrategy(mapping=mapping)
        pii = "secret-api-key-abc123"
        detections = s.scan_value("unknown_field", pii)
        result = s.redact(pii, detections)
        assert pii not in result


# -- Integration-style: full field processing --------------------------------


class TestFullFieldProcessing:
    """End-to-end field processing through scan_value then redact."""

    def test_process_email_field_redact(self) -> None:
        mapping = FieldMapping({"email": RedactionAction.REDACT})
        s = StrictStrategy(mapping=mapping)
        value = "jane.smith@testmail.org"
        detections = s.scan_value("email", value)
        result = s.redact(value, detections)
        assert result == "[EMAIL_REDACTED]"
        assert "jane.smith" not in result

    def test_process_email_field_mask(self) -> None:
        mapping = FieldMapping({"email": RedactionAction.MASK})
        s = StrictStrategy(mapping=mapping)
        value = "jane.smith@testmail.org"
        detections = s.scan_value("email", value)
        result = s.redact(value, detections)
        assert result == "j***@testmail.org"
        assert "jane.smith" not in result

    def test_process_name_field_hash(self) -> None:
        mapping = FieldMapping({"name": RedactionAction.HASH})
        s = StrictStrategy(mapping=mapping)
        value = "Bob Wilson"
        detections = s.scan_value("name", value)
        result = s.redact(value, detections)
        assert result.startswith("hash_")
        assert "Bob" not in result
        assert "Wilson" not in result

    def test_process_model_field_keep(self) -> None:
        mapping = FieldMapping({"model": RedactionAction.KEEP})
        s = StrictStrategy(mapping=mapping)
        value = "gpt-4"
        detections = s.scan_value("model", value)
        assert detections == []
        result = s.redact(value, detections)
        assert result == "gpt-4"

    def test_process_multiple_fields_with_different_actions(self) -> None:
        mapping = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "name": RedactionAction.MASK,
                "user_id": RedactionAction.HASH,
                "model": RedactionAction.KEEP,
            }
        )
        s = StrictStrategy(mapping=mapping)

        record = {
            "email": "john@example.com",
            "name": "John Doe",
            "user_id": "uid-42",
            "model": "gpt-4",
        }

        results: dict[str, str] = {}
        for key, value in record.items():
            detections = s.scan_value(key, value)
            results[key] = s.redact(value, detections)

        assert results["email"] == "[EMAIL_REDACTED]"
        assert results["name"] == "J***e"
        assert results["user_id"].startswith("hash_")
        assert results["model"] == "gpt-4"

        # PII leak checks
        assert "john@example.com" not in str(results)
        assert "John Doe" not in str(results)
        assert "uid-42" not in str(results)


# -- IsA RedactionStrategy ---------------------------------------------------


class TestStrictStrategyIsRedactionStrategy:
    """StrictStrategy is a proper subclass of RedactionStrategy."""

    def test_is_subclass_of_redaction_strategy(self) -> None:
        from cecil.core.sanitizer.strategies import RedactionStrategy

        assert issubclass(StrictStrategy, RedactionStrategy)

    def test_instance_is_redaction_strategy(
        self,
        strategy: StrictStrategy,
    ) -> None:
        from cecil.core.sanitizer.strategies import RedactionStrategy

        assert isinstance(strategy, RedactionStrategy)


# -- Coverage: mapping returns None guard (line 188) -------------------------


class TestScanValueMappingReturnsNone:
    """When FieldMapping.get() returns None, scan_value defaults to REDACT."""

    def test_scan_value_none_action_defaults_to_redact(self) -> None:
        mapping = FieldMapping({})
        mapping._mappings["broken"] = None  # type: ignore[assignment]
        s = StrictStrategy(mapping=mapping)
        detections = s.scan_value("broken", "value")
        assert len(detections) == 1
        assert detections[0].entity_type == "REDACT"


# -- Coverage: unknown entity_type fallback (line 244) -----------------------


class TestRedactUnknownActionFallback:
    """When detection has unrecognised entity_type, redact returns value."""

    def test_redact_unknown_action_returns_original(self) -> None:
        from cecil.core.sanitizer.models import Detection

        mapping = FieldMapping({"f": RedactionAction.REDACT})
        s = StrictStrategy(mapping=mapping)
        dets = [Detection(entity_type="UNKNOWN", start=0, end=5, score=1.0)]
        assert s.redact("hello", dets) == "hello"
