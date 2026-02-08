"""Shared test fixtures for provider unit tests.

Provides temporary file fixtures (JSONL, CSV, malformed) used by
the LocalFileProvider and other provider test suites.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.pii_samples import (
    generate_sample_csv,
    generate_sample_jsonl,
    generate_sample_parquet,
)


@pytest.fixture()
def tmp_jsonl_path(tmp_path: Path) -> Path:
    """Create a temporary JSONL file with sample PII records.

    Returns:
        Path to a temporary JSONL file containing 5 records.
    """
    path = tmp_path / "sample.jsonl"
    generate_sample_jsonl(str(path), count=5)
    return path


@pytest.fixture()
def tmp_csv_path(tmp_path: Path) -> Path:
    """Create a temporary CSV file with sample PII records.

    Returns:
        Path to a temporary CSV file containing 5 records.
    """
    path = tmp_path / "sample.csv"
    generate_sample_csv(str(path), count=5)
    return path


@pytest.fixture()
def malformed_jsonl_path(tmp_path: Path) -> Path:
    """Create a temporary JSONL file with malformed JSON on the third line.

    The file contains two valid JSON lines followed by one invalid line.

    Returns:
        Path to a temporary JSONL file with a parse error on line 3.
    """
    path = tmp_path / "malformed.jsonl"
    lines = [
        json.dumps({"id": 1, "value": "ok"}),
        json.dumps({"id": 2, "value": "also ok"}),
        "NOT VALID JSON {{{",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def empty_jsonl_path(tmp_path: Path) -> Path:
    """Create a temporary empty JSONL file.

    Returns:
        Path to an empty JSONL file.
    """
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    return path


@pytest.fixture()
def blank_lines_jsonl_path(tmp_path: Path) -> Path:
    """Create a JSONL file with blank lines interspersed.

    Returns:
        Path to a JSONL file containing 2 valid records and blank lines.
    """
    path = tmp_path / "blanks.jsonl"
    lines = [
        "",
        json.dumps({"id": 1}),
        "",
        "   ",
        json.dumps({"id": 2}),
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def tmp_parquet_path(tmp_path: Path) -> Path:
    """Create a temporary Parquet file with sample PII records.

    Returns:
        Path to a temporary Parquet file containing 5 records.
    """
    path = tmp_path / "sample.parquet"
    generate_sample_parquet(str(path), count=5)
    return path
