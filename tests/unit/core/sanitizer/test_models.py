"""Tests for sanitization domain models, types, and RedactionStrategy ABC.

Covers every public type exported from ``cecil.core.sanitizer.models``
and the ``RedactionStrategy`` abstract base class from
``cecil.core.sanitizer.strategies``, plus the sanitization error
hierarchy in ``cecil.utils.errors``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

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
from cecil.core.sanitizer.strategies import RedactionStrategy
from cecil.utils.errors import (
    CecilError,
    MappingError,
    MappingFileError,
    MappingValidationError,
    RecordSanitizationError,
    SanitizationError,
)


# -- RedactionAction enum ---------------------------------------------------


class TestRedactionAction:
    """Tests for the RedactionAction enumeration."""

    def test_redaction_action_has_four_members(self) -> None:
        """The enum exposes exactly four action types."""
        assert len(RedactionAction) == 4

    def test_redaction_action_values_are_correct(self) -> None:
        """Each member has the expected lowercase string value."""
        assert RedactionAction.REDACT.value == "redact"
        assert RedactionAction.MASK.value == "mask"
        assert RedactionAction.HASH.value == "hash"
        assert RedactionAction.KEEP.value == "keep"

    def test_redaction_action_from_value(self) -> None:
        """An action can be constructed from its string value."""
        assert RedactionAction("redact") is RedactionAction.REDACT
        assert RedactionAction("keep") is RedactionAction.KEEP

    def test_redaction_action_invalid_value_raises_value_error(self) -> None:
        """Constructing from an unknown string raises ValueError."""
        with pytest.raises(ValueError):
            RedactionAction("unknown")

    def test_redaction_action_is_iterable(self) -> None:
        """All members can be iterated over as a sequence."""
        members = list(RedactionAction)
        assert len(members) == 4
        assert RedactionAction.REDACT in members
        assert RedactionAction.MASK in members
        assert RedactionAction.HASH in members
        assert RedactionAction.KEEP in members


# -- StreamErrorPolicy enum -------------------------------------------------


class TestStreamErrorPolicy:
    """Tests for the StreamErrorPolicy enumeration."""

    def test_stream_error_policy_has_two_members(self) -> None:
        """The enum exposes exactly two policy options."""
        assert len(StreamErrorPolicy) == 2

    def test_stream_error_policy_skip_and_abort(self) -> None:
        """Both SKIP_RECORD and ABORT_STREAM carry correct string values."""
        assert StreamErrorPolicy.SKIP_RECORD.value == "skip_record"
        assert StreamErrorPolicy.ABORT_STREAM.value == "abort_stream"


# -- Detection dataclass -----------------------------------------------------


class TestDetection:
    """Tests for the Detection frozen dataclass."""

    def test_detection_creation(self) -> None:
        """A Detection can be created with all four required fields."""
        d = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        assert isinstance(d, Detection)

    def test_detection_fields_accessible(self) -> None:
        """All Detection attributes are accessible after construction."""
        d = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        assert d.entity_type == "EMAIL"
        assert d.start == 0
        assert d.end == 20
        assert d.score == 0.95

    def test_detection_is_frozen(self) -> None:
        """Attempting to mutate any attribute raises AttributeError."""
        d = Detection(entity_type="SSN", start=5, end=16, score=0.99)
        with pytest.raises(AttributeError):
            d.entity_type = "PHONE"  # type: ignore[misc]

    def test_detection_score_is_required(self) -> None:
        """Score has no default value and must be provided explicitly."""
        with pytest.raises(TypeError):
            Detection(entity_type="EMAIL", start=0, end=20)  # type: ignore[call-arg]

    def test_detection_equality(self) -> None:
        """Two Detections with identical fields are equal."""
        d1 = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        d2 = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        assert d1 == d2

    def test_detection_inequality_on_different_fields(self) -> None:
        """Two Detections differing in any field are not equal."""
        d1 = Detection(entity_type="EMAIL", start=0, end=20, score=0.95)
        d2 = Detection(entity_type="SSN", start=0, end=20, score=0.95)
        assert d1 != d2


# -- FieldRedaction dataclass ------------------------------------------------


class TestFieldRedaction:
    """Tests for the FieldRedaction frozen dataclass."""

    def test_field_redaction_creation(self) -> None:
        """A FieldRedaction stores all four required fields correctly."""
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

    def test_field_redaction_is_frozen(self) -> None:
        """Attempting to mutate any attribute raises AttributeError."""
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
    """Tests for the RedactionAudit frozen dataclass."""

    def test_redaction_audit_creation(self) -> None:
        """A RedactionAudit can be created with record_id and fields_redacted."""
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

    def test_redaction_audit_default_timestamp(self) -> None:
        """An audit created without a timestamp gets a UTC timestamp automatically."""
        before = datetime.now(UTC)
        audit = RedactionAudit(record_id="rec-002", fields_redacted=[])
        after = datetime.now(UTC)
        assert before <= audit.timestamp <= after
        assert audit.timestamp.tzinfo is not None

    def test_redaction_audit_accepts_custom_timestamp(self) -> None:
        """An explicit timestamp overrides the auto-generated default."""
        ts = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        audit = RedactionAudit(
            record_id="rec-003",
            fields_redacted=[],
            timestamp=ts,
        )
        assert audit.timestamp == ts

    def test_redaction_audit_fields_redacted_list(self) -> None:
        """The fields_redacted list correctly stores multiple FieldRedaction items."""
        fr_email = FieldRedaction(
            field_name="email",
            action=RedactionAction.REDACT,
            entity_type="EMAIL",
            count=1,
        )
        fr_ssn = FieldRedaction(
            field_name="ssn",
            action=RedactionAction.MASK,
            entity_type="SSN",
            count=2,
        )
        fr_phone = FieldRedaction(
            field_name="phone",
            action=RedactionAction.REDACT,
            entity_type="PHONE",
            count=1,
        )
        audit = RedactionAudit(
            record_id="rec-005",
            fields_redacted=[fr_email, fr_ssn, fr_phone],
        )
        assert len(audit.fields_redacted) == 3
        field_names = [fr.field_name for fr in audit.fields_redacted]
        assert field_names == ["email", "ssn", "phone"]

    def test_redaction_audit_is_frozen(self) -> None:
        """Attempting to mutate any attribute raises AttributeError."""
        audit = RedactionAudit(record_id="rec-004", fields_redacted=[])
        with pytest.raises(AttributeError):
            audit.record_id = "changed"  # type: ignore[misc]


# -- SanitizedRecord dataclass -----------------------------------------------


class TestSanitizedRecord:
    """Tests for the SanitizedRecord frozen dataclass."""

    def test_sanitized_record_creation(self) -> None:
        """A SanitizedRecord can be created with data dict and audit."""
        audit = RedactionAudit(record_id="rec-010", fields_redacted=[])
        record = SanitizedRecord(
            data={"name": "[NAME_REDACTED]", "model": "gpt-4"},
            audit=audit,
        )
        assert isinstance(record, SanitizedRecord)

    def test_sanitized_record_has_data_and_audit(self) -> None:
        """The data dict and audit are accessible on the record."""
        audit = RedactionAudit(record_id="rec-010", fields_redacted=[])
        record = SanitizedRecord(
            data={"name": "[NAME_REDACTED]", "model": "gpt-4"},
            audit=audit,
        )
        assert record.data["name"] == "[NAME_REDACTED]"
        assert record.data["model"] == "gpt-4"
        assert record.audit is audit

    def test_sanitized_record_is_frozen(self) -> None:
        """Attempting to reassign data or audit raises AttributeError."""
        audit = RedactionAudit(record_id="rec-011", fields_redacted=[])
        record = SanitizedRecord(data={"key": "val"}, audit=audit)
        with pytest.raises(AttributeError):
            record.data = {}  # type: ignore[misc]


# -- FieldMapping class ------------------------------------------------------


class TestFieldMapping:
    """Tests for the FieldMapping dict-like wrapper."""

    def test_field_mapping_empty_mapping(self) -> None:
        """A FieldMapping created with no arguments is empty."""
        fm = FieldMapping()
        assert len(fm) == 0

    def test_field_mapping_creation_with_dict(self) -> None:
        """A FieldMapping can be created from a dict of field-to-action pairs."""
        fm = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "name": RedactionAction.MASK,
            },
        )
        assert len(fm) == 2

    def test_field_mapping_get_action_returns_mapped_action(self) -> None:
        """Subscript access returns the mapped RedactionAction for a known field."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm["email"] is RedactionAction.REDACT

    def test_field_mapping_get_action_returns_default_for_unmapped(self) -> None:
        """The get() method returns a caller-provided default for unmapped fields."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm.get("missing") is None
        assert fm.get("missing", RedactionAction.KEEP) is RedactionAction.KEEP

    def test_field_mapping_default_action_is_none_when_unset(self) -> None:
        """The get() method returns None by default for unmapped fields."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm.get("unmapped_field") is None

    def test_field_mapping_custom_default_action(self) -> None:
        """The get() method accepts a custom default RedactionAction."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        result = fm.get("unknown_field", RedactionAction.REDACT)
        assert result is RedactionAction.REDACT

    def test_field_mapping_getitem_missing_raises_key_error(self) -> None:
        """Subscript access for an unmapped field raises KeyError."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        with pytest.raises(KeyError):
            fm["nonexistent"]

    def test_field_mapping_contains_check(self) -> None:
        """The in operator correctly reports field membership."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert "email" in fm
        assert "missing" not in fm

    def test_field_mapping_len(self) -> None:
        """len() returns the number of mapped fields."""
        fm_empty = FieldMapping()
        fm_two = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "name": RedactionAction.MASK,
            },
        )
        assert len(fm_empty) == 0
        assert len(fm_two) == 2

    def test_field_mapping_iter(self) -> None:
        """Iterating yields all mapped field names."""
        fm = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "name": RedactionAction.MASK,
            },
        )
        keys = list(fm)
        assert set(keys) == {"email", "name"}

    def test_field_mapping_items(self) -> None:
        """items() returns (field_name, action) pairs."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        items = list(fm.items())
        assert items == [("email", RedactionAction.REDACT)]

    def test_field_mapping_keys_and_values(self) -> None:
        """keys() and values() return the expected views."""
        fm = FieldMapping(
            {
                "email": RedactionAction.REDACT,
                "safe": RedactionAction.KEEP,
            },
        )
        assert set(fm.keys()) == {"email", "safe"}
        assert set(fm.values()) == {RedactionAction.REDACT, RedactionAction.KEEP}

    def test_field_mapping_repr(self) -> None:
        """repr() includes the class name and field contents."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        r = repr(fm)
        assert r.startswith("FieldMapping(")
        assert "email" in r

    def test_field_mapping_equality(self) -> None:
        """Two FieldMappings with identical contents are equal."""
        fm1 = FieldMapping({"email": RedactionAction.REDACT})
        fm2 = FieldMapping({"email": RedactionAction.REDACT})
        assert fm1 == fm2

    def test_field_mapping_inequality(self) -> None:
        """Two FieldMappings with different contents are not equal."""
        fm1 = FieldMapping({"email": RedactionAction.REDACT})
        fm2 = FieldMapping({"email": RedactionAction.KEEP})
        assert fm1 != fm2

    def test_field_mapping_equality_with_non_mapping_returns_not_implemented(self) -> None:
        """Equality with a non-FieldMapping type returns NotImplemented."""
        fm = FieldMapping({"email": RedactionAction.REDACT})
        assert fm != "not a mapping"

    def test_field_mapping_none_creates_empty(self) -> None:
        """Passing None explicitly to the constructor creates an empty mapping."""
        fm = FieldMapping(None)
        assert len(fm) == 0


# -- RedactionStrategy ABC ---------------------------------------------------


class TestRedactionStrategy:
    """Tests for the RedactionStrategy abstract base class."""

    def test_redaction_strategy_cannot_be_instantiated(self) -> None:
        """The ABC itself cannot be directly instantiated."""
        with pytest.raises(TypeError):
            RedactionStrategy()  # type: ignore[abstract]

    def test_redaction_strategy_subclass_must_implement_scan_value(self) -> None:
        """A subclass implementing only redact (missing scan_value) cannot be instantiated."""

        class OnlyRedact(RedactionStrategy):
            def redact(self, value: str, detections: list[Detection]) -> str:
                return value

        with pytest.raises(TypeError):
            OnlyRedact()  # type: ignore[abstract]

    def test_redaction_strategy_subclass_must_implement_redact(self) -> None:
        """A subclass implementing only scan_value (missing redact) cannot be instantiated."""

        class OnlyScanValue(RedactionStrategy):
            def scan_value(self, key: str, value: Any) -> list[Detection]:
                return []

        with pytest.raises(TypeError):
            OnlyScanValue()  # type: ignore[abstract]

    def test_redaction_strategy_subclass_with_neither_method_cannot_be_instantiated(
        self,
    ) -> None:
        """A subclass implementing neither abstract method cannot be instantiated."""

        class IncompleteStrategy(RedactionStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteStrategy()  # type: ignore[abstract]

    def test_redaction_strategy_complete_subclass_works(self) -> None:
        """A subclass implementing both methods can be instantiated and used."""

        class ConcreteStrategy(RedactionStrategy):
            def scan_value(self, key: str, value: Any) -> list[Detection]:
                return []

            def redact(self, value: str, detections: list[Detection]) -> str:
                return value

        strategy = ConcreteStrategy()
        assert strategy.scan_value("field", "value") == []
        assert strategy.redact("hello", []) == "hello"

    def test_redaction_strategy_scan_value_returns_detections(self) -> None:
        """A concrete strategy can detect PII and produce Detection objects."""

        class FakeStrategy(RedactionStrategy):
            def scan_value(self, key: str, value: Any) -> list[Detection]:
                if key == "email":
                    return [
                        Detection(
                            entity_type="EMAIL",
                            start=0,
                            end=len(str(value)),
                            score=0.99,
                        ),
                    ]
                return []

            def redact(self, value: str, detections: list[Detection]) -> str:
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
    """Tests for the sanitization error class hierarchy."""

    def test_record_sanitization_error_inherits_sanitization_error(self) -> None:
        """RecordSanitizationError is a subclass of SanitizationError."""
        assert issubclass(RecordSanitizationError, SanitizationError)

    def test_record_sanitization_error_inherits_cecil_error(self) -> None:
        """RecordSanitizationError ultimately inherits from CecilError."""
        assert issubclass(RecordSanitizationError, CecilError)

    def test_record_sanitization_error_can_be_raised_and_caught(self) -> None:
        """A RecordSanitizationError can be caught as SanitizationError."""
        with pytest.raises(SanitizationError):
            raise RecordSanitizationError("record failed")

    def test_record_sanitization_error_can_be_caught_as_cecil_error(self) -> None:
        """A RecordSanitizationError can be caught as CecilError at the top level."""
        with pytest.raises(CecilError):
            raise RecordSanitizationError("record failed")

    def test_record_sanitization_error_message(self) -> None:
        """The error message is preserved in the exception string."""
        err = RecordSanitizationError("field parse failure in record abc-123")
        assert "abc-123" in str(err)


# -- FieldMappingEntry dataclass -----------------------------------------------


class TestFieldMappingEntry:
    """Tests for the FieldMappingEntry frozen dataclass."""

    def test_field_mapping_entry_creation_stores_action_and_options(self) -> None:
        """A FieldMappingEntry stores the action and custom options."""
        entry = FieldMappingEntry(
            action=RedactionAction.MASK,
            options={"preserve_domain": True},
        )
        assert entry.action is RedactionAction.MASK
        assert entry.options == {"preserve_domain": True}

    def test_field_mapping_entry_default_options_empty_dict(self) -> None:
        """When no options are provided, the default is an empty dict."""
        entry = FieldMappingEntry(action=RedactionAction.REDACT)
        assert entry.options == {}

    def test_field_mapping_entry_frozen_raises_on_assignment(self) -> None:
        """Attempting to mutate any attribute raises AttributeError."""
        entry = FieldMappingEntry(action=RedactionAction.KEEP)
        with pytest.raises(AttributeError):
            entry.action = RedactionAction.HASH  # type: ignore[misc]


# -- MappingConfig dataclass ---------------------------------------------------


class TestMappingConfig:
    """Tests for the MappingConfig frozen dataclass."""

    def test_mapping_config_creation_stores_all_fields(self) -> None:
        """A MappingConfig stores version, default_action, and fields."""
        fields = {
            "email": FieldMappingEntry(action=RedactionAction.REDACT),
            "name": FieldMappingEntry(
                action=RedactionAction.MASK,
                options={"preserve_first": True},
            ),
        }
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields=fields,
        )
        assert config.version == 1
        assert config.default_action is RedactionAction.KEEP
        assert len(config.fields) == 2
        assert config.fields["email"].action is RedactionAction.REDACT
        assert config.fields["name"].options == {"preserve_first": True}

    def test_mapping_config_policy_hash_returns_hex_string(self) -> None:
        """policy_hash() returns a 64-character hexadecimal SHA-256 digest."""
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields={
                "email": FieldMappingEntry(action=RedactionAction.REDACT),
            },
        )
        h = config.policy_hash()
        assert isinstance(h, str)
        assert len(h) == 64
        # Verify it's a valid hex string
        int(h, 16)

    def test_mapping_config_policy_hash_deterministic_same_config(self) -> None:
        """The same config produces the same hash on repeated calls."""
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "ssn": FieldMappingEntry(action=RedactionAction.REDACT),
                "email": FieldMappingEntry(action=RedactionAction.MASK),
            },
        )
        assert config.policy_hash() == config.policy_hash()

    def test_mapping_config_policy_hash_differs_for_different_configs(self) -> None:
        """Two configs with different fields produce different hashes."""
        config_a = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields={
                "email": FieldMappingEntry(action=RedactionAction.REDACT),
            },
        )
        config_b = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields={
                "email": FieldMappingEntry(action=RedactionAction.MASK),
            },
        )
        assert config_a.policy_hash() != config_b.policy_hash()

    def test_mapping_config_frozen_raises_on_assignment(self) -> None:
        """Attempting to mutate any attribute raises AttributeError."""
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields={},
        )
        with pytest.raises(AttributeError):
            config.version = 2  # type: ignore[misc]


# -- MappingValidationResult dataclass ----------------------------------------


class TestMappingValidationResult:
    """Tests for the MappingValidationResult frozen dataclass."""

    def test_mapping_validation_result_is_valid_true_when_no_missing(self) -> None:
        """is_valid is True when missing_fields is empty."""
        result = MappingValidationResult(
            matched_fields=["email", "name"],
            unmapped_fields=["model"],
            missing_fields=[],
        )
        assert result.is_valid is True

    def test_mapping_validation_result_is_valid_false_when_missing_fields(self) -> None:
        """is_valid is False when missing_fields is non-empty."""
        result = MappingValidationResult(
            matched_fields=["email"],
            unmapped_fields=[],
            missing_fields=["ssn"],
        )
        assert result.is_valid is False

    def test_mapping_validation_result_stores_all_field_lists(self) -> None:
        """All three field lists are stored and accessible."""
        result = MappingValidationResult(
            matched_fields=["email", "name"],
            unmapped_fields=["model", "timestamp"],
            missing_fields=["ssn"],
        )
        assert result.matched_fields == ["email", "name"]
        assert result.unmapped_fields == ["model", "timestamp"]
        assert result.missing_fields == ["ssn"]


# -- Mapping error hierarchy ---------------------------------------------------


class TestMappingErrors:
    """Tests for the mapping-specific error classes."""

    def test_mapping_error_inherits_from_sanitization_error(self) -> None:
        """MappingError is a subclass of SanitizationError."""
        assert issubclass(MappingError, SanitizationError)

    def test_mapping_validation_error_inherits_from_mapping_error(self) -> None:
        """MappingValidationError is a subclass of MappingError."""
        assert issubclass(MappingValidationError, MappingError)

    def test_mapping_file_error_inherits_from_mapping_error(self) -> None:
        """MappingFileError is a subclass of MappingError."""
        assert issubclass(MappingFileError, MappingError)

    def test_mapping_error_can_be_caught_as_cecil_error(self) -> None:
        """All mapping errors can be caught with except CecilError."""
        with pytest.raises(CecilError):
            raise MappingError("mapping issue")

    def test_mapping_validation_error_can_be_caught_as_cecil_error(self) -> None:
        """MappingValidationError can be caught with except CecilError."""
        with pytest.raises(CecilError):
            raise MappingValidationError("invalid schema")

    def test_mapping_file_error_can_be_caught_as_cecil_error(self) -> None:
        """MappingFileError can be caught with except CecilError."""
        with pytest.raises(CecilError):
            raise MappingFileError("cannot read file")


# -- MappingConfig policy_hash with multiple fields ----------------------------


class TestMappingConfigPolicyHashMultiField:
    """Verify policy_hash covers multiple fields and options."""

    def test_policy_hash_includes_options_in_digest(self) -> None:
        """Options are part of the hash payload so they affect the digest."""
        config_with_opts = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "email": FieldMappingEntry(
                    action=RedactionAction.MASK,
                    options={"preserve_domain": True},
                ),
            },
        )
        config_without_opts = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "email": FieldMappingEntry(
                    action=RedactionAction.MASK,
                    options={},
                ),
            },
        )
        assert config_with_opts.policy_hash() != config_without_opts.policy_hash()

    def test_policy_hash_empty_fields_is_valid(self) -> None:
        """policy_hash on a config with no fields produces a valid hex digest."""
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields={},
        )
        h = config.policy_hash()
        assert len(h) == 64
        int(h, 16)  # Must be valid hex

    def test_mapping_validation_result_frozen_raises_on_assignment(self) -> None:
        """MappingValidationResult is frozen and cannot be mutated."""
        result = MappingValidationResult(
            matched_fields=["a"],
            unmapped_fields=["b"],
            missing_fields=["c"],
        )
        with pytest.raises(AttributeError):
            result.matched_fields = []  # type: ignore[misc]
