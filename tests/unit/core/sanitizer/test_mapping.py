"""Tests for MappingParser -- mapping.yaml loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cecil.core.sanitizer.mapping import MappingParser, validate_mapping_against_record
from cecil.core.sanitizer.models import (
    FieldMappingEntry,
    MappingConfig,
    RedactionAction,
)
from cecil.utils.errors import MappingFileError, MappingValidationError


@pytest.fixture()
def parser() -> MappingParser:
    """Return a fresh MappingParser instance."""
    return MappingParser()


def _valid_data(
    *,
    version: int = 1,
    default_action: str | None = None,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a minimal valid mapping dict, with optional overrides."""
    data: dict[str, Any] = {
        "version": version,
        "fields": fields or {"email": {"action": "redact"}},
    }
    if default_action is not None:
        data["default_action"] = default_action
    return data


def _write_yaml(tmp_path: Path, content: str, name: str = "mapping.yaml") -> Path:
    """Write YAML content to a temp file and return its path."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# -- File-based tests ------------------------------------------------------


class TestParseFile:
    """Tests for MappingParser.parse_file()."""

    def test_parse_file_valid_yaml_returns_mapping_config(
        self,
        parser: MappingParser,
        tmp_path: Path,
    ) -> None:
        """A well-formed mapping.yaml is parsed into a MappingConfig."""
        yaml_content = """\
version: 1
default_action: keep
fields:
  email:
    action: redact
  name:
    action: mask
    preserve_length: true
"""
        path = _write_yaml(tmp_path, yaml_content)
        config = parser.parse_file(path)

        assert isinstance(config, MappingConfig)
        assert config.version == 1
        assert config.default_action == RedactionAction.KEEP
        assert len(config.fields) == 2
        assert config.fields["email"].action == RedactionAction.REDACT
        assert config.fields["name"].action == RedactionAction.MASK
        assert config.fields["name"].options == {"preserve_length": True}

    def test_parse_file_not_found_raises_mapping_file_error(
        self,
        parser: MappingParser,
        tmp_path: Path,
    ) -> None:
        """A non-existent file raises MappingFileError."""
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(MappingFileError, match="not found"):
            parser.parse_file(missing)

    def test_parse_file_os_error_raises_mapping_file_error(
        self,
        parser: MappingParser,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An OS-level read error (e.g., permission denied) raises MappingFileError."""
        path = _write_yaml(tmp_path, "version: 1\nfields:\n  a:\n    action: redact\n")

        def _raise_oserror(*_args: Any, **_kwargs: Any) -> str:
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "read_text", _raise_oserror)
        with pytest.raises(MappingFileError, match="Cannot read"):
            parser.parse_file(path)

    def test_parse_file_invalid_yaml_syntax_raises_mapping_file_error(
        self,
        parser: MappingParser,
        tmp_path: Path,
    ) -> None:
        """Malformed YAML raises MappingFileError."""
        path = _write_yaml(tmp_path, ":\n  - :\n  bad: [unterminated")
        with pytest.raises(MappingFileError, match="Invalid YAML"):
            parser.parse_file(path)

    def test_parse_file_non_dict_yaml_raises_validation_error(
        self,
        parser: MappingParser,
        tmp_path: Path,
    ) -> None:
        """A YAML file containing a list (not dict) raises MappingValidationError."""
        path = _write_yaml(tmp_path, "- item1\n- item2\n")
        with pytest.raises(MappingValidationError, match="YAML mapping"):
            parser.parse_file(path)


# -- Dict-based tests ------------------------------------------------------


class TestParseDict:
    """Tests for MappingParser.parse_dict()."""

    def test_parse_dict_valid_returns_mapping_config(
        self,
        parser: MappingParser,
    ) -> None:
        """A valid dict is correctly converted to MappingConfig."""
        data = _valid_data(default_action="keep")
        config = parser.parse_dict(data)

        assert config.version == 1
        assert config.default_action == RedactionAction.KEEP
        assert "email" in config.fields
        assert config.fields["email"].action == RedactionAction.REDACT

    def test_parse_dict_missing_version_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """Missing 'version' key raises MappingValidationError."""
        data = {"fields": {"email": {"action": "redact"}}}
        with pytest.raises(MappingValidationError, match="version"):
            parser.parse_dict(data)

    def test_parse_dict_unsupported_version_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """An unsupported version number raises MappingValidationError."""
        data = _valid_data(version=99)
        with pytest.raises(MappingValidationError, match="Unsupported"):
            parser.parse_dict(data)

    def test_parse_dict_missing_fields_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """Missing 'fields' key raises MappingValidationError."""
        data: dict[str, Any] = {"version": 1}
        with pytest.raises(MappingValidationError, match="fields"):
            parser.parse_dict(data)

    def test_parse_dict_empty_fields_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """An empty 'fields' dict raises MappingValidationError."""
        data: dict[str, Any] = {"version": 1, "fields": {}}
        with pytest.raises(MappingValidationError, match="at least one"):
            parser.parse_dict(data)

    def test_parse_dict_fields_not_dict_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """'fields' as a list (not dict) raises MappingValidationError."""
        data: dict[str, Any] = {"version": 1, "fields": ["email"]}
        with pytest.raises(MappingValidationError, match=r"mapping.*dict"):
            parser.parse_dict(data)

    def test_parse_dict_invalid_action_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """An unrecognised action value raises MappingValidationError."""
        data = _valid_data(fields={"email": {"action": "nuke"}})
        with pytest.raises(MappingValidationError, match="Invalid action"):
            parser.parse_dict(data)

    def test_parse_dict_default_action_defaults_to_redact(
        self,
        parser: MappingParser,
    ) -> None:
        """Omitting default_action results in REDACT."""
        data = _valid_data()  # no default_action
        config = parser.parse_dict(data)
        assert config.default_action == RedactionAction.REDACT

    def test_parse_dict_explicit_default_action_preserved(
        self,
        parser: MappingParser,
    ) -> None:
        """An explicit default_action is respected."""
        data = _valid_data(default_action="hash")
        config = parser.parse_dict(data)
        assert config.default_action == RedactionAction.HASH

    def test_parse_dict_invalid_default_action_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """An invalid default_action raises MappingValidationError."""
        data = _valid_data(default_action="destroy")
        with pytest.raises(MappingValidationError, match="Invalid action"):
            parser.parse_dict(data)

    def test_parse_dict_action_case_insensitive(
        self,
        parser: MappingParser,
    ) -> None:
        """Action values are case-insensitive."""
        data = _valid_data(
            fields={
                "a": {"action": "REDACT"},
                "b": {"action": "Mask"},
                "c": {"action": "HASH"},
                "d": {"action": "Keep"},
            },
        )
        config = parser.parse_dict(data)
        assert config.fields["a"].action == RedactionAction.REDACT
        assert config.fields["b"].action == RedactionAction.MASK
        assert config.fields["c"].action == RedactionAction.HASH
        assert config.fields["d"].action == RedactionAction.KEEP

    def test_parse_dict_action_specific_options_preserved(
        self,
        parser: MappingParser,
    ) -> None:
        """Extra keys beside 'action' are captured in options."""
        data = _valid_data(
            fields={
                "email": {
                    "action": "mask",
                    "preserve_domain": True,
                    "mask_char": "*",
                },
            },
        )
        config = parser.parse_dict(data)
        entry = config.fields["email"]
        assert entry.action == RedactionAction.MASK
        assert entry.options == {"preserve_domain": True, "mask_char": "*"}

    def test_parse_dict_not_dict_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """Passing a non-dict to parse_dict raises MappingValidationError."""
        with pytest.raises(MappingValidationError, match="must be a dict"):
            parser.parse_dict("not a dict")  # type: ignore[arg-type]

    def test_parse_dict_all_four_actions_accepted(
        self,
        parser: MappingParser,
    ) -> None:
        """All four RedactionAction values are accepted as field actions."""
        data = _valid_data(
            fields={
                "f1": {"action": "redact"},
                "f2": {"action": "mask"},
                "f3": {"action": "hash"},
                "f4": {"action": "keep"},
            },
        )
        config = parser.parse_dict(data)
        assert config.fields["f1"].action == RedactionAction.REDACT
        assert config.fields["f2"].action == RedactionAction.MASK
        assert config.fields["f3"].action == RedactionAction.HASH
        assert config.fields["f4"].action == RedactionAction.KEEP

    def test_parse_dict_field_config_not_dict_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """A field whose config is not a dict raises MappingValidationError."""
        data = _valid_data(fields={"email": "redact"})
        with pytest.raises(MappingValidationError, match="must be a dict"):
            parser.parse_dict(data)

    def test_parse_dict_field_missing_action_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """A field config without 'action' key raises MappingValidationError."""
        data = _valid_data(fields={"email": {"preserve_domain": True}})
        with pytest.raises(MappingValidationError, match="missing required key 'action'"):
            parser.parse_dict(data)

    def test_parse_dict_action_not_string_raises_validation_error(
        self,
        parser: MappingParser,
    ) -> None:
        """A non-string action value (e.g., int) raises MappingValidationError."""
        data = _valid_data(fields={"email": {"action": 42}})
        with pytest.raises(MappingValidationError, match="expected a string"):
            parser.parse_dict(data)


# -- Validation against sample records --------------------------------------


def _make_config(
    field_names: list[str],
    *,
    default_action: RedactionAction = RedactionAction.REDACT,
) -> MappingConfig:
    """Build a MappingConfig with the given field names (all REDACT)."""
    return MappingConfig(
        version=1,
        default_action=default_action,
        fields={name: FieldMappingEntry(action=RedactionAction.REDACT) for name in field_names},
    )


class TestValidateMappingAgainstRecord:
    """Tests for validate_mapping_against_record()."""

    def test_validate_all_fields_match_returns_valid(self) -> None:
        """When mapping and record share all keys, result is valid."""
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "email": FieldMappingEntry(action=RedactionAction.MASK),
                "name": FieldMappingEntry(action=RedactionAction.REDACT),
            },
        )
        record = {"email": "test@example.com", "name": "John"}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is True
        assert result.matched_fields == ["email", "name"]
        assert result.unmapped_fields == []
        assert result.missing_fields == []

    def test_validate_mapping_field_not_in_record_appears_in_missing(self) -> None:
        """A mapping field absent from the record is reported as missing."""
        config = _make_config(["email", "ssn"])
        record = {"email": "test@example.com"}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is False
        assert "ssn" in result.missing_fields
        assert "email" in result.matched_fields
        assert result.unmapped_fields == []

    def test_validate_record_field_not_in_mapping_appears_in_unmapped(self) -> None:
        """A record field absent from the mapping is reported as unmapped."""
        config = _make_config(["email"])
        record = {"email": "test@example.com", "phone": "555-0100"}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is True
        assert "phone" in result.unmapped_fields
        assert result.matched_fields == ["email"]
        assert result.missing_fields == []

    def test_validate_partial_overlap_reports_all_categories(self) -> None:
        """When there is partial overlap, all three categories are populated."""
        config = _make_config(["email", "ssn", "dob"])
        record = {"email": "a@b.com", "phone": "555-0100", "address": "123 Main"}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is False
        assert result.matched_fields == ["email"]
        assert result.unmapped_fields == ["address", "phone"]
        assert result.missing_fields == ["dob", "ssn"]

    def test_validate_empty_mapping_fields_returns_valid(self) -> None:
        """A mapping with no fields (constructed directly) is always valid."""
        config = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={},
        )
        record = {"email": "test@example.com", "name": "John"}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is True
        assert result.matched_fields == []
        assert result.unmapped_fields == ["email", "name"]
        assert result.missing_fields == []

    def test_validate_empty_record_reports_all_mapping_fields_missing(self) -> None:
        """An empty record means every mapping field is missing."""
        config = _make_config(["email", "name"])
        record: dict[str, str] = {}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is False
        assert result.matched_fields == []
        assert result.unmapped_fields == []
        assert result.missing_fields == ["email", "name"]

    def test_validate_no_overlap_reports_all_unmapped_and_missing(self) -> None:
        """Completely disjoint fields populate both unmapped and missing."""
        config = _make_config(["ssn", "dob"])
        record = {"phone": "555-0100", "address": "123 Main"}
        result = validate_mapping_against_record(config, record)

        assert result.is_valid is False
        assert result.matched_fields == []
        assert result.unmapped_fields == ["address", "phone"]
        assert result.missing_fields == ["dob", "ssn"]

    def test_validate_matched_fields_are_sorted(self) -> None:
        """Matched fields are returned in sorted order."""
        config = _make_config(["zebra", "apple", "mango"])
        record = {"zebra": "z", "apple": "a", "mango": "m"}
        result = validate_mapping_against_record(config, record)

        assert result.matched_fields == ["apple", "mango", "zebra"]

    def test_validate_unmapped_fields_are_sorted(self) -> None:
        """Unmapped fields are returned in sorted order."""
        config = _make_config(["x"])
        record = {"x": "1", "zebra": "z", "apple": "a", "mango": "m"}
        result = validate_mapping_against_record(config, record)

        assert result.unmapped_fields == ["apple", "mango", "zebra"]

    def test_validate_missing_fields_are_sorted(self) -> None:
        """Missing fields are returned in sorted order."""
        config = _make_config(["zebra", "apple", "mango"])
        record: dict[str, str] = {}
        result = validate_mapping_against_record(config, record)

        assert result.missing_fields == ["apple", "mango", "zebra"]


# -- MappingConfig policy_hash edge cases -------------------------------------


class TestMappingConfigPolicyHashEdgeCases:
    """Additional edge-case tests for policy_hash determinism."""

    def test_policy_hash_with_options_differs_from_without(self) -> None:
        """Two configs differing only in options produce different hashes."""
        config_a = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "email": FieldMappingEntry(
                    action=RedactionAction.MASK,
                    options={"preserve_domain": True},
                ),
            },
        )
        config_b = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "email": FieldMappingEntry(
                    action=RedactionAction.MASK,
                    options={},
                ),
            },
        )
        assert config_a.policy_hash() != config_b.policy_hash()

    def test_policy_hash_with_different_default_action_differs(self) -> None:
        """Two configs with different default_action produce different hashes."""
        config_a = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={"f": FieldMappingEntry(action=RedactionAction.KEEP)},
        )
        config_b = MappingConfig(
            version=1,
            default_action=RedactionAction.KEEP,
            fields={"f": FieldMappingEntry(action=RedactionAction.KEEP)},
        )
        assert config_a.policy_hash() != config_b.policy_hash()

    def test_policy_hash_field_order_independent(self) -> None:
        """Fields are sorted before hashing so order does not matter."""
        config_a = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields={
                "a": FieldMappingEntry(action=RedactionAction.REDACT),
                "b": FieldMappingEntry(action=RedactionAction.MASK),
            },
        )
        # Same fields but inserted in reverse order
        from collections import OrderedDict

        fields_reversed = OrderedDict(
            [
                ("b", FieldMappingEntry(action=RedactionAction.MASK)),
                ("a", FieldMappingEntry(action=RedactionAction.REDACT)),
            ],
        )
        config_b = MappingConfig(
            version=1,
            default_action=RedactionAction.REDACT,
            fields=dict(fields_reversed),
        )
        assert config_a.policy_hash() == config_b.policy_hash()


# -- MappingParser action whitespace/case edge cases --------------------------


class TestMappingParserActionEdgeCases:
    """Edge-case tests for action parsing."""

    def test_parse_action_with_leading_trailing_whitespace(self) -> None:
        """Action values with whitespace are trimmed and normalized."""
        parser = MappingParser()
        data = _valid_data(fields={"email": {"action": "  REDACT  "}})
        config = parser.parse_dict(data)
        assert config.fields["email"].action == RedactionAction.REDACT

    def test_parse_action_mixed_case(self) -> None:
        """Mixed-case action values are normalized."""
        parser = MappingParser()
        data = _valid_data(fields={"email": {"action": "ReDaCt"}})
        config = parser.parse_dict(data)
        assert config.fields["email"].action == RedactionAction.REDACT
