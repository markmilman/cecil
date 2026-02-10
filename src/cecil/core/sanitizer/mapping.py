"""Mapping.yaml parser and schema validation.

Loads user-defined mapping configuration files, validates their
structure, and produces ``MappingConfig`` instances for use by
the sanitization pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from cecil.core.sanitizer.models import (
    FieldMappingEntry,
    MappingConfig,
    MappingValidationResult,
    RedactionAction,
)
from cecil.utils.errors import MappingFileError, MappingValidationError


logger = logging.getLogger(__name__)

_SUPPORTED_VERSIONS: frozenset[int] = frozenset({1})


class MappingParser:
    """Parser for mapping.yaml configuration files.

    Loads a YAML file, validates its structure against the mapping
    schema (version, default_action, fields), and returns a
    ``MappingConfig`` instance.

    The parser validates:
    - version is present and supported (currently only version 1)
    - fields is a non-empty dict
    - Each field has a valid RedactionAction
    - Action-specific options are preserved in FieldMappingEntry
    - default_action defaults to REDACT if omitted
    """

    def parse_file(self, path: Path | str) -> MappingConfig:
        """Parse a mapping.yaml file from disk.

        Args:
            path: Path to the mapping.yaml file.

        Returns:
            A validated MappingConfig instance.

        Raises:
            MappingFileError: If the file cannot be read or has invalid YAML.
            MappingValidationError: If the schema is invalid.
        """
        file_path = Path(path)
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except FileNotFoundError as err:
            raise MappingFileError(
                f"Mapping file not found: {file_path}",
            ) from err
        except OSError as err:
            raise MappingFileError(
                f"Cannot read mapping file: {file_path}",
            ) from err

        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as err:
            raise MappingFileError(
                f"Invalid YAML syntax in {file_path}: {err}",
            ) from err

        if not isinstance(data, dict):
            raise MappingValidationError(
                "Mapping file must contain a YAML mapping (dict) at the top level",
            )

        return self.parse_dict(data)

    def parse_dict(self, data: dict[str, Any]) -> MappingConfig:
        """Parse a mapping configuration from an already-loaded dict.

        Args:
            data: The raw mapping dictionary (e.g., from yaml.safe_load).

        Returns:
            A validated MappingConfig.

        Raises:
            MappingValidationError: If the schema is invalid.
        """
        if not isinstance(data, dict):
            raise MappingValidationError(
                "Mapping data must be a dict",
            )

        # -- version --------------------------------------------------------
        if "version" not in data:
            raise MappingValidationError(
                "Missing required key 'version' in mapping configuration",
            )
        version = data["version"]
        if version not in _SUPPORTED_VERSIONS:
            raise MappingValidationError(
                f"Unsupported mapping version {version!r}; "
                f"supported versions: {sorted(_SUPPORTED_VERSIONS)}",
            )

        # -- default_action -------------------------------------------------
        default_action = self._parse_action(
            data.get("default_action", "redact"),
            context="default_action",
        )

        # -- fields ---------------------------------------------------------
        if "fields" not in data:
            raise MappingValidationError(
                "Missing required key 'fields' in mapping configuration",
            )
        raw_fields = data["fields"]
        if not isinstance(raw_fields, dict):
            raise MappingValidationError(
                "'fields' must be a mapping (dict) of field names to configurations",
            )
        if len(raw_fields) == 0:
            raise MappingValidationError(
                "'fields' must contain at least one field entry",
            )

        fields: dict[str, FieldMappingEntry] = {}
        for field_name, field_cfg in raw_fields.items():
            if not isinstance(field_cfg, dict):
                raise MappingValidationError(
                    f"Field '{field_name}' configuration must be a dict",
                )
            if "action" not in field_cfg:
                raise MappingValidationError(
                    f"Field '{field_name}' is missing required key 'action'",
                )
            action = self._parse_action(
                field_cfg["action"],
                context=f"fields.{field_name}.action",
            )
            options = {k: v for k, v in field_cfg.items() if k != "action"}
            fields[field_name] = FieldMappingEntry(
                action=action,
                options=options,
            )

        config = MappingConfig(
            version=version,
            default_action=default_action,
            fields=fields,
        )

        logger.debug(
            "mapping_parsed version=%d field_count=%d default_action=%s",
            config.version,
            len(config.fields),
            config.default_action.value,
        )

        return config

    @staticmethod
    def _parse_action(value: Any, *, context: str) -> RedactionAction:
        """Parse and validate a redaction action string.

        Args:
            value: The raw action value (expected to be a string).
            context: A human-readable context for error messages.

        Returns:
            The corresponding ``RedactionAction`` enum member.

        Raises:
            MappingValidationError: If the value is not a valid action.
        """
        if not isinstance(value, str):
            raise MappingValidationError(
                f"Invalid action for {context}: expected a string, got {type(value).__name__}",
            )
        normalised = value.strip().lower()
        try:
            return RedactionAction(normalised)
        except ValueError:
            valid = [a.value for a in RedactionAction]
            raise MappingValidationError(
                f"Invalid action '{value}' for {context}; valid actions: {valid}",
            ) from None


def validate_mapping_against_record(
    config: MappingConfig,
    record: dict[str, Any],
) -> MappingValidationResult:
    """Validate a mapping configuration against a sample record.

    Compares the field names defined in the mapping with the keys
    present in the sample record to identify:

    - matched_fields: fields in both the mapping and the record
    - unmapped_fields: fields in the record but not in the mapping
    - missing_fields: fields in the mapping but not in the record

    This pre-validation step ensures the mapping is compatible with
    the actual data schema before processing the full dataset.

    Args:
        config: The parsed mapping configuration.
        record: A sample data record (dict with string keys).

    Returns:
        A MappingValidationResult with match/unmatch/missing field lists.
    """
    mapping_fields = set(config.fields.keys())
    record_fields = set(record.keys())

    matched = sorted(mapping_fields & record_fields)
    unmapped = sorted(record_fields - mapping_fields)
    missing = sorted(mapping_fields - record_fields)

    result = MappingValidationResult(
        matched_fields=matched,
        unmapped_fields=unmapped,
        missing_fields=missing,
    )

    logger.debug(
        "mapping_validation matched=%d unmapped=%d missing=%d is_valid=%s",
        len(matched),
        len(unmapped),
        len(missing),
        result.is_valid,
    )

    return result
