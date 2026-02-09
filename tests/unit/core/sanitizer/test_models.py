"""Tests for sanitization domain models, types, and RedactionStrategy ABC."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cecil.core.sanitizer.models import (
    Detection,
    FieldMapping,
    FieldRedaction,
    RedactionAction,
    RedactionAudit,
    SanitizedRecord,
    StreamErrorPolicy,
)
from cecil.core.sanitizer.strategies import RedactionStrategy
from cecil.utils.errors import RecordSanitizationError, SanitizationError


# -- RedactionAction enum ---------------------------------------------------


class TestRedactionAction:
    def test_redaction_action_has_four_members(self):
        assert len(RedactionAction) == 4

    def test_redaction_action_values(self):
        assert RedactionAction.REDACT.value == "redact"
        assert RedactionAction.MASK.value == "mask"
        assert RedactionAction.HASH.value == "hash"
        assert RedactionAction.KEEP.value == "keep"

    def test_redaction_action_from_value(self):
        assert RedactionAction("redact") is RedactionAction.REDACT
        assert RedactionAction("keep") is RedactionAction.KEEP

    def test_redaction_action_invalid_value_raises_value_error(self):
        with pytest.raises(ValueError):
            RedactionAction("unknown")


# -- StreamErrorPolicy enum -------------------------------------------------


class TestStreamErrorPolicy:
    def test_stream_error_policy_has_two_members(self):
        assert len(StreamErrorPolicy) == 2

    def test_stream_error_policy_values(self):
        assert StreamErrorPolicy.SKIP_RECORD.value == "skip_record"
        assert StreamErrorPolicy.ABORT_STREAM.value == "abort_stream"


# -- Detection dataclass -----------------------------------------------------


class TestDetection:
    def test_detection_stores_all_fields(self):
        d = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        assert d.entity_type == "EMAIL"
        assert d.start == 0
        assert d.end == 20
        assert d.score == 0.95

    def test_detection_is_frozen(self):
        d = Detection(entity_type="SSN", start=5, end=16, score=0.99)
        with pytest.raises(AttributeError):
            d.entity_type = "PHONE"  # type: ignore[misc]

    def test_detection_equality(self):
        d1 = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        d2 = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        assert d1 == d2

    def test_detection_inequality_on_different_fields(self):
        d1 = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        d2 = Detection(entity_type="SSN", start=0, end=20, score=0.95)
        assert d1 != d2


# -- FieldRedaction dataclass ------------------------------------------------


class TestFieldRedaction:
    def test_field_redaction_stores_all_fields(self):
        fr = FieldRedaction(
            field_name="email",
            action=RedactionAction.REDACT,
            entity_type="EMAIL",
            count=1,
        )
        assert fr.field_name == "email"
        assert fr.action is RedactionAction.REDACT
        assert fr.entity_type == "EMAIL"
        assert fr.count == 1

    def test_field_redaction_is_frozen(self):
        fr = FieldRedaction(
            field_name="ssn",
            action=RedactionAction.MASK,
            entity_type="SSN",
            count=2,
        )
        with pytest.raises(AttributeError):
            fr.count = 5  # type: ignore[misc]


# -- RedactionAudit dataclass ------------------------------------------------


class TestRedactionAudit:
    def test_redaction_audit_stores_required_fields(self):
        fr = FieldRedaction(
            field_name="email",
            action=RedactionAction.REDACT,
            entity_type="EMAIL",
            count=1,
        )
        audit = RedactionAudit(
            record_id="rec-001",
            fields_redacted=[fr],
        )
        assert audit.record_id == "rec-001"
        assert len(audit.fields_redacted) == 1
        assert audit.fields_redacted[0] is fr

    def test_redaction_audit_has_utc_timestamp_by_default(self):
        before = datetime.now(UTC)
        audit = RedactionAudit(record_id="rec-002", fields_redacted=[])
        after = datetime.now(UTC)
        assert before <= audit.timestamp <= after
        assert audit.timestamp.tzinfo is not None

    def test_redaction_audit_accepts_custom_timestamp(self):
        ts = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        audit = RedactionAudit(
            record_id="rec-003",
            fields_redacted=[],
            timestamp=ts,
        )
        assert audit.timestamp == ts

    def test_redaction_audit_is_frozen(self):
        audit = RedactionAudit(record_id="rec-004", fields_redacted=[])
        with pytest.raises(AttributeError):
            audit.record_id = "changed"  # type: ignore[misc]


# -- SanitizedRecord dataclass -----------------------------------------------


class TestSanitizedRecord:
    def test_sanitized_record_stores_data_and_audit(self):
        audit = RedactionAudit(record_id="rec-010", fields_redacted=[])
        record = SanitizedRecord(
            data={"name": "[NAME_REDACTED]", "model": "gpt-4"},
            audit=audit,
        )
        assert record.data["name"] == "[NAME_REDACTED]"
        assert record.data["model"] == "gpt-4"
        assert record.audit is audit

    def test_sanitized_record_is_frozen(self):
        audit = RedactionAudit(record_id="rec-011", fields_redacted=[])
        record = SanitizedRecord(data={"key": "val"}, audit=audit)
        with pytest.raises(AttributeError):
            record.data = {}  # type: ignore[misc]


# -- FieldMapping class ------------------------------------------------------


class TestFieldMapping:
    def test_field_mapping_empty_by_default(self):
        fm = FieldMapping()
        assert len(fm) == 0

    def test_field_mapping_from_dict(self):
        fm = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "name": RedactionAction.MASK,
            }
        )
        assert len(fm) == 2

    def test_field_mapping_getitem(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm["email"] is RedactionAction.REDACT

    def test_field_mapping_getitem_missing_raises_key_error(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        with pytest.raises(KeyError):
            fm["nonexistent"]

    def test_field_mapping_contains(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert "email" in fm
        assert "missing" not in fm

    def test_field_mapping_get_with_default(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm.get("email") is RedactionAction.REDACT
        assert fm.get("missing") is None
        assert fm.get("missing", RedactionAction.KEEP) is RedactionAction.KEEP

    def test_field_mapping_iter(self):
        fm = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "name": RedactionAction.MASK,
            }
        )
        keys = list(fm)
        assert set(keys) == {"email", "name"}

    def test_field_mapping_items(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        items = list(fm.items())
        assert items == [("email", RedactionAction.REDACT)]

    def test_field_mapping_keys_and_values(self):
        fm = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "safe": RedactionAction.KEEP,
            }
        )
        assert set(fm.keys()) == {"email", "safe"}
        assert set(fm.values()) == {RedactionAction.REDACT, RedactionAction.KEEP}

    def test_field_mapping_repr(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        r = repr(fm)
        assert r.startswith("FieldMapping(")
        assert "email" in r

    def test_field_mapping_equality(self):
        fm1 = FieldMapping({"email": RedactionAction.REDACT})
        fm2 = FieldMapping({"email": RedactionAction.REDACT})
        assert fm1 == fm2

    def test_field_mapping_inequality(self):
        fm1 = FieldMapping({"email": RedactionAction.REDACT})
        fm2 = FieldMapping({"email": RedactionAction.KEEP})
        assert fm1 != fm2

    def test_field_mapping_equality_with_non_mapping_returns_not_implemented(self):
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm != "not a mapping"

    def test_field_mapping_none_creates_empty(self):
        fm = FieldMapping(None)
        assert len(fm) == 0


# -- RedactionStrategy ABC ---------------------------------------------------


class TestRedactionStrategy:
    def test_redaction_strategy_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            RedactionStrategy()  # type: ignore[abstract]

    def test_concrete_strategy_must_implement_scan_value_and_redact(self):
        class IncompleteStrategy(RedactionStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteStrategy()  # type: ignore[abstract]

    def test_concrete_strategy_with_both_methods_can_be_instantiated(self):
        class ConcreteStrategy(RedactionStrategy):
            def scan_value(self, key, value):
                return []

            def redact(self, value, detections):
                return value

        strategy = ConcreteStrategy()
        assert strategy.scan_value("field", "value") == []
        assert strategy.redact("hello", []) == "hello"

    def test_concrete_strategy_scan_value_returns_detections(self):
        class FakeStrategy(RedactionStrategy):
            def scan_value(self, key, value):
                if key == "email":
                    return [
                        Detection(
                            entity_type="EMAIL",
                            start=0,
                            end=len(str(value)),
                            score=0.99,
                        )
                    ]
                return []

            def redact(self, value, detections):
                result = value
                for d in sorted(detections, key=lambda x: x.start, reverse=True):
                    result = result[: d.start] + f"[{d.entity_type}_REDACTED]" + result[d.end :]
                return result

        strategy = FakeStrategy()
        detections = strategy.scan_value("email", "test@example.com")
        assert len(detections) == 1
        assert detections[0].entity_type == "EMAIL"

        redacted = strategy.redact("test@example.com", detections)
        assert "test@example.com" not in redacted
        assert "[EMAIL_REDACTED]" in redacted


# -- RecordSanitizationError hierarchy ---------------------------------------


class TestRecordSanitizationError:
    def test_record_sanitization_error_inherits_from_sanitization_error(self):
        assert issubclass(RecordSanitizationError, SanitizationError)

    def test_record_sanitization_error_can_be_raised_and_caught(self):
        with pytest.raises(SanitizationError):
            raise RecordSanitizationError("record failed")

    def test_record_sanitization_error_message(self):
        err = RecordSanitizationError("field parse failure in record abc-123")
        assert "abc-123" in str(err)
