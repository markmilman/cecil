"""Unit tests for the PII fixture data generator.

Validates that the fixture generator produces deterministic,
well-structured data with known PII values that can be used
for leak detection assertions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.pii_samples import (
    KNOWN_PII_BUNDLES,
    KnownPII,
    all_known_pii_values,
    generate_pii_batch,
    generate_sample_csv,
    generate_sample_jsonl,
    make_llm_log_record,
    make_log_records_from_bundles,
    stream_log_records,
)


class TestKnownPII:
    """Verify the KnownPII dataclass and constants."""

    def test_known_pii_is_frozen_dataclass(self):
        """Verify KnownPII instances are immutable."""
        pii = KNOWN_PII_BUNDLES[0]
        with pytest.raises(AttributeError):
            pii.email = "changed@example.com"  # type: ignore[misc]

    def test_known_pii_all_values_returns_all_fields(self):
        """Verify all_values includes every field."""
        pii = KNOWN_PII_BUNDLES[0]
        values = pii.all_values()
        assert len(values) == 8
        assert pii.email in values
        assert pii.ssn in values
        assert pii.phone in values
        assert pii.name in values
        assert pii.address in values
        assert pii.credit_card in values
        assert pii.ip_address in values
        assert pii.date_of_birth in values

    def test_known_pii_bundles_have_unique_emails(self):
        """Verify each bundle has a distinct email for identification."""
        emails = [b.email for b in KNOWN_PII_BUNDLES]
        assert len(emails) == len(set(emails))

    def test_known_pii_bundles_have_unique_ssns(self):
        """Verify each bundle has a distinct SSN."""
        ssns = [b.ssn for b in KNOWN_PII_BUNDLES]
        assert len(ssns) == len(set(ssns))


class TestAllKnownPIIValues:
    """Verify the aggregated PII values helper."""

    def test_returns_flat_list(self):
        """Verify all_known_pii_values returns a flat list of strings."""
        values = all_known_pii_values()
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)

    def test_count_matches_bundles_times_fields(self):
        """Verify count is bundles * fields_per_bundle."""
        values = all_known_pii_values()
        expected = len(KNOWN_PII_BUNDLES) * 8
        assert len(values) == expected


class TestGeneratePIIBatch:
    """Verify the faker-based PII batch generator."""

    def test_generates_requested_count(self):
        """Verify the batch contains the requested number of identities."""
        batch = generate_pii_batch(count=5)
        assert len(batch.identities) == 5

    def test_all_pii_values_populated(self):
        """Verify the flat PII values list is populated."""
        batch = generate_pii_batch(count=3)
        assert len(batch.all_pii_values) == 3 * 8

    def test_deterministic_output(self):
        """Verify two calls with the same count produce identical output."""
        batch1 = generate_pii_batch(count=5)
        batch2 = generate_pii_batch(count=5)
        assert batch1.all_pii_values == batch2.all_pii_values

    def test_identities_are_known_pii_instances(self):
        """Verify each identity is a KnownPII instance."""
        batch = generate_pii_batch(count=2)
        for identity in batch.identities:
            assert isinstance(identity, KnownPII)


class TestMakeLLMLogRecord:
    """Verify the LLM log record factory."""

    def test_record_contains_pii_email(self):
        """Verify the record embeds the PII email."""
        pii = KNOWN_PII_BUNDLES[0]
        record = make_llm_log_record(pii)
        assert record["user_email"] == pii.email

    def test_record_contains_pii_in_prompt(self):
        """Verify the prompt field contains embedded PII."""
        pii = KNOWN_PII_BUNDLES[0]
        record = make_llm_log_record(pii)
        assert pii.name in record["prompt"]
        assert pii.ssn in record["prompt"]
        assert pii.email in record["prompt"]

    def test_record_contains_nested_pii(self):
        """Verify PII exists in nested metadata fields."""
        pii = KNOWN_PII_BUNDLES[0]
        record = make_llm_log_record(pii)
        assert record["metadata"]["credit_card_on_file"] == pii.credit_card
        assert record["metadata"]["dob"] == pii.date_of_birth

    def test_record_contains_model_field(self):
        """Verify the model field is set correctly."""
        record = make_llm_log_record(KNOWN_PII_BUNDLES[0], model="claude-3")
        assert record["model"] == "claude-3"

    def test_record_contains_cost_fields(self):
        """Verify non-PII cost fields are present."""
        record = make_llm_log_record(KNOWN_PII_BUNDLES[0])
        assert "tokens_in" in record
        assert "tokens_out" in record
        assert "cost_usd" in record


class TestMakeLogRecordsFromBundles:
    """Verify the batch log record factory."""

    def test_returns_one_record_per_bundle(self):
        """Verify default call returns one record per known bundle."""
        records = make_log_records_from_bundles()
        assert len(records) == len(KNOWN_PII_BUNDLES)

    def test_each_record_has_distinct_email(self):
        """Verify each record has a unique user email."""
        records = make_log_records_from_bundles()
        emails = [r["user_email"] for r in records]
        assert len(emails) == len(set(emails))

    def test_custom_bundles(self):
        """Verify custom bundles can be provided."""
        subset = KNOWN_PII_BUNDLES[:1]
        records = make_log_records_from_bundles(bundles=subset)
        assert len(records) == 1


class TestStreamLogRecords:
    """Verify the streaming log record generator."""

    def test_yields_requested_count(self):
        """Verify the generator yields the exact count."""
        records = list(stream_log_records(count=7))
        assert len(records) == 7

    def test_cycles_through_bundles(self):
        """Verify records cycle through known PII bundles."""
        count = len(KNOWN_PII_BUNDLES) * 2
        records = list(stream_log_records(count=count))

        # First and (N+1)th records should have the same email
        for i in range(len(KNOWN_PII_BUNDLES)):
            assert records[i]["user_email"] == records[i + len(KNOWN_PII_BUNDLES)]["user_email"]

    def test_zero_count_yields_nothing(self):
        """Verify count=0 produces an empty generator."""
        records = list(stream_log_records(count=0))
        assert records == []


class TestGenerateSampleJSONL:
    """Verify the JSONL fixture file generator."""

    def test_creates_valid_jsonl_file(self, tmp_path: Path):
        """Verify the output is valid JSONL (one JSON object per line)."""
        path = str(tmp_path / "test.jsonl")
        generate_sample_jsonl(path, count=3)

        lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        for line in lines:
            parsed = json.loads(line)
            assert isinstance(parsed, dict)

    def test_returns_pii_values_list(self, tmp_path: Path):
        """Verify the function returns the embedded PII values."""
        path = str(tmp_path / "test.jsonl")
        pii_values = generate_sample_jsonl(path, count=3)
        assert len(pii_values) > 0
        assert all(isinstance(v, str) for v in pii_values)


class TestGenerateSampleCSV:
    """Verify the CSV fixture file generator."""

    def test_creates_valid_csv_file(self, tmp_path: Path):
        """Verify the output is a valid CSV with header and data rows."""
        path = str(tmp_path / "test.csv")
        generate_sample_csv(path, count=3)

        lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 4  # 1 header + 3 data rows

    def test_csv_header_contains_expected_columns(self, tmp_path: Path):
        """Verify the CSV header has the expected column names."""
        path = str(tmp_path / "test.csv")
        generate_sample_csv(path, count=1)

        header = Path(path).read_text(encoding="utf-8").splitlines()[0]
        for col in ["email", "name", "ssn", "phone"]:
            assert col in header

    def test_returns_pii_values_list(self, tmp_path: Path):
        """Verify the function returns the embedded PII values."""
        path = str(tmp_path / "test.csv")
        pii_values = generate_sample_csv(path, count=3)
        assert len(pii_values) > 0
