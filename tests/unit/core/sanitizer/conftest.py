"""Shared pytest fixtures for sanitizer unit tests.

Provides pre-built MappingConfig instances, sample records,
and file-based mapping fixtures for sanitizer test suites.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cecil.core.sanitizer.models import (
    FieldMappingEntry,
    MappingConfig,
    RedactionAction,
)


FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures"


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture()
def valid_mapping_path(fixtures_dir: Path) -> Path:
    """Return the path to the valid mapping.yaml fixture."""
    return fixtures_dir / "mapping_valid.yaml"


@pytest.fixture()
def all_actions_mapping_path(fixtures_dir: Path) -> Path:
    """Return the path to the all-actions mapping.yaml fixture."""
    return fixtures_dir / "mapping_all_actions.yaml"


@pytest.fixture()
def invalid_action_mapping_path(fixtures_dir: Path) -> Path:
    """Return the path to the invalid-action mapping.yaml fixture."""
    return fixtures_dir / "mapping_invalid_action.yaml"


@pytest.fixture()
def invalid_version_mapping_path(fixtures_dir: Path) -> Path:
    """Return the path to the invalid-version mapping.yaml fixture."""
    return fixtures_dir / "mapping_invalid_version.yaml"


@pytest.fixture()
def minimal_mapping_path(fixtures_dir: Path) -> Path:
    """Return the path to the minimal mapping.yaml fixture."""
    return fixtures_dir / "mapping_minimal.yaml"


@pytest.fixture()
def sample_mapping_config() -> MappingConfig:
    """Return a MappingConfig with all four action types.

    Fields:
    - user_email: MASK (preserve_domain=true)
    - session_id: HASH
    - request_body: REDACT
    - model_name: KEEP
    - timestamp: KEEP
    """
    return MappingConfig(
        version=1,
        default_action=RedactionAction.REDACT,
        fields={
            "user_email": FieldMappingEntry(
                action=RedactionAction.MASK,
                options={"preserve_domain": True},
            ),
            "session_id": FieldMappingEntry(action=RedactionAction.HASH),
            "request_body": FieldMappingEntry(action=RedactionAction.REDACT),
            "model_name": FieldMappingEntry(action=RedactionAction.KEEP),
            "timestamp": FieldMappingEntry(action=RedactionAction.KEEP),
        },
    )


@pytest.fixture()
def sample_record() -> dict[str, Any]:
    """Return a sample data record matching the valid mapping fields.

    Contains realistic but non-real PII data for testing.
    """
    return {
        "user_email": "alice@example.com",
        "session_id": "sess-abc-123-def-456",
        "request_body": "Tell me about quantum computing",
        "model_name": "gpt-4",
        "timestamp": "2024-01-15T10:30:00Z",
    }


@pytest.fixture()
def sample_record_with_extra_fields(sample_record: dict[str, Any]) -> dict[str, Any]:
    """Return a sample record with fields not in the mapping."""
    return {
        **sample_record,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
    }


@pytest.fixture()
def tmp_mapping_file(tmp_path: Path) -> Path:
    """Return a path for a temporary mapping.yaml file.

    The file does not exist yet -- callers should write content to it.
    """
    return tmp_path / "mapping.yaml"
