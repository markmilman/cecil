"""Shared test fixtures for the Cecil test suite.

Provides PII fixture data, mock providers pre-loaded with known PII,
and temporary file helpers used across unit, integration, and E2E tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cecil.core.providers.mock import MockDataProvider
from tests.fixtures.pii_samples import (
    KNOWN_PII_BUNDLES,
    KnownPII,
    all_known_pii_values,
    make_log_records_from_bundles,
)


# ── Path helpers ─────────────────────────────────────────────────────


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the absolute path to the ``tests/fixtures/`` directory.

    Returns:
        Path to the fixtures directory.
    """
    return FIXTURES_DIR


@pytest.fixture()
def sample_jsonl_path() -> Path:
    """Return the path to the sample JSONL log fixture file.

    Returns:
        Path to ``tests/fixtures/sample_logs.jsonl``.
    """
    return FIXTURES_DIR / "sample_logs.jsonl"


@pytest.fixture()
def sample_csv_path() -> Path:
    """Return the path to the sample CSV fixture file.

    Returns:
        Path to ``tests/fixtures/sample_records.csv``.
    """
    return FIXTURES_DIR / "sample_records.csv"


# ── PII fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def known_pii_bundles() -> list[KnownPII]:
    """Return the hard-coded PII bundles used in test fixtures.

    Returns:
        A list of ``KnownPII`` dataclass instances.
    """
    return list(KNOWN_PII_BUNDLES)


@pytest.fixture()
def known_pii_values() -> list[str]:
    """Return a flat list of every known PII string value.

    Useful for asserting that none of these strings appear in
    sanitized output.

    Returns:
        A list of all PII string values across all bundles.
    """
    return all_known_pii_values()


# ── Provider fixtures ────────────────────────────────────────────────


@pytest.fixture()
def pii_log_records() -> list[dict[str, Any]]:
    """Return log records containing embedded PII from all known bundles.

    Returns:
        A list of LLM API log record dictionaries with embedded PII.
    """
    return make_log_records_from_bundles()


@pytest.fixture()
def mock_provider_with_pii(
    pii_log_records: list[dict[str, Any]],
) -> MockDataProvider:
    """Return a connected MockDataProvider pre-loaded with PII records.

    The provider is connected and ready to stream.

    Args:
        pii_log_records: Log records containing embedded PII.

    Returns:
        A connected ``MockDataProvider`` instance.
    """
    provider = MockDataProvider(records=pii_log_records)
    provider.connect()
    return provider
